"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

entry point
"""

import os
import sys
import time
import fnmatch
from concurrent import futures

# local imports
from dotdrop.options import Options
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
from dotdrop.installer import Installer
from dotdrop.updater import Updater
from dotdrop.comparator import Comparator
from dotdrop.importer import Importer
from dotdrop.utils import get_tmpdir, removepath, \
    uniq_list, patch_ignores, dependencies_met, \
    adapt_workers, check_version, pivot_path
from dotdrop.linktypes import LinkTypes
from dotdrop.exceptions import YamlException, \
    UndefinedException, UnmetDependency

LOG = Logger()
TRANS_SUFFIX = 'trans'

###########################################################
# entry point
###########################################################


def action_executor(opts, actions, defactions, templater, post=False):
    """closure for action execution"""
    def execute():
        """
        execute actions and return
        True, None if ok
        False, errstring if issue
        """
        actiontype = 'pre' if not post else 'post'

        # execute default actions
        for action in defactions:
            if opts.dry:
                LOG.dry('would execute def-{}-action: {}'.format(actiontype,
                                                                 action))
                continue
            LOG.dbg('executing def-{}-action: {}'.format(actiontype, action))
            ret = action.execute(templater=templater, debug=opts.debug)
            if not ret:
                err = 'def-{}-action \"{}\" failed'
                LOG.err(err.format(actiontype, action.key))
                return False, err

        # execute actions
        for action in actions:
            if opts.dry:
                err = 'would execute {}-action: {}'
                LOG.dry(err.format(actiontype, action))
                continue
            LOG.dbg('executing {}-action: {}'.format(actiontype, action))
            ret = action.execute(templater=templater, debug=opts.debug)
            if not ret:
                err = '{}-action \"{}\" failed'.format(actiontype, action.key)
                LOG.err(err)
                return False, err
        return True, None
    return execute


def _dotfile_update(opts, path, key=False):
    """
    update a dotfile pointed by path
    if key is false or by key (in path)
    """
    updater = Updater(opts.dotpath, opts.variables, opts.conf, opts.profile,
                      dry=opts.dry, safe=opts.safe, debug=opts.debug,
                      ignore=opts.update_ignore,
                      showpatch=opts.update_showpatch,
                      ignore_missing_in_dotdrop=opts.ignore_missing_in_dotdrop)
    if key:
        return updater.update_key(path)
    return updater.update_path(path)


def _dotfile_compare(opts, dotfile, tmp):
    """
    compare a dotfile
    returns True if same
    """
    templ = _get_templater(opts)
    ignore_missing_in_dotdrop = opts.ignore_missing_in_dotdrop or \
        dotfile.ignore_missing_in_dotdrop
    inst = Installer(create=opts.create, backup=opts.backup,
                     dry=opts.dry, base=opts.dotpath,
                     workdir=opts.workdir, debug=opts.debug,
                     backup_suffix=opts.install_backup_suffix,
                     diff_cmd=opts.diff_command)
    comp = Comparator(diff_cmd=opts.diff_command, debug=opts.debug,
                      ignore_missing_in_dotdrop=ignore_missing_in_dotdrop)

    # add dotfile variables
    newvars = dotfile.get_dotfile_variables()
    templ.add_tmp_vars(newvars=newvars)

    # dotfiles does not exist / not installed
    LOG.dbg('comparing {}'.format(dotfile))

    src = dotfile.src
    if not os.path.lexists(os.path.expanduser(dotfile.dst)):
        line = '=> compare {}: \"{}\" does not exist on destination'
        LOG.log(line.format(dotfile.key, dotfile.dst))
        return False

    # apply transformation
    tmpsrc = None
    if dotfile.trans_r:
        LOG.dbg('applying transformation before comparing')
        tmpsrc = apply_trans(opts.dotpath, dotfile, templ, debug=opts.debug)
        if not tmpsrc:
            # could not apply trans
            return False
        src = tmpsrc

    # is a symlink pointing to itself
    asrc = os.path.join(opts.dotpath, os.path.expanduser(src))
    adst = os.path.expanduser(dotfile.dst)
    if os.path.samefile(asrc, adst):
        line = '=> compare {}: diffing with \"{}\"'
        LOG.dbg(line.format(dotfile.key, dotfile.dst))
        LOG.dbg('points to itself')
        return True

    ignores = list(set(opts.compare_ignore + dotfile.cmpignore))
    ignores = patch_ignores(ignores, dotfile.dst, debug=opts.debug)

    insttmp = None
    if dotfile.template and Templategen.is_template(src,
                                                    ignore=ignores,
                                                    debug=opts.debug):
        # install dotfile to temporary dir for compare
        ret, err, insttmp = inst.install_to_temp(templ, tmp, src, dotfile.dst,
                                                 is_template=True,
                                                 chmod=dotfile.chmod,
                                                 set_create=True)
        if not ret:
            # failed to install to tmp
            line = '=> compare {} error: {}'
            LOG.log(line.format(dotfile.key, err))
            LOG.err(err)
            return False
        src = insttmp

    # compare
    # need to be executed before cleaning
    diff = comp.compare(src, dotfile.dst, ignore=ignores)

    # clean tmp transformed dotfile if any
    if tmpsrc:
        tmpsrc = os.path.join(opts.dotpath, tmpsrc)
        if os.path.exists(tmpsrc):
            removepath(tmpsrc, LOG)

    # clean tmp template dotfile if any
    if insttmp and os.path.exists(insttmp):
        removepath(insttmp, LOG)

    if diff != '':
        # print diff results
        if opts.compare_fileonly:
            line = '=> differ: \"{}\" \"{}\"'.format(dotfile.src, dotfile.dst)
            LOG.log(line.format(dotfile.key, dotfile.dst))
        else:
            line = '=> compare {}: diffing with \"{}\"'
            LOG.log(line.format(dotfile.key, dotfile.dst))
            LOG.emph(diff)
        return False

    # no difference
    line = '=> compare {}: diffing with \"{}\"'
    LOG.dbg(line.format(dotfile.key, dotfile.dst))
    LOG.dbg('same file')
    return True


def _dotfile_install(opts, dotfile, tmpdir=None):
    """
    install a dotfile
    returns <success, dotfile key, err>
    """
    # installer
    inst = _get_install_installer(opts, tmpdir=tmpdir)

    # templater
    templ = _get_templater(opts)

    # add dotfile variables
    newvars = dotfile.get_dotfile_variables()
    templ.add_tmp_vars(newvars=newvars)

    preactions = []
    if not opts.install_temporary:
        preactions.extend(dotfile.get_pre_actions())
    defactions = opts.install_default_actions_pre
    pre_actions_exec = action_executor(opts, preactions, defactions,
                                       templ, post=False)

    LOG.dbg('installing dotfile: \"{}\"'.format(dotfile.key))
    LOG.dbg(dotfile.prt())

    ignores = list(set(opts.install_ignore + dotfile.instignore))
    ignores = patch_ignores(ignores, dotfile.dst, debug=opts.debug)

    is_template = dotfile.template and Templategen.is_template(
        dotfile.src,
        ignore=ignores,
    )
    if hasattr(dotfile, 'link') and dotfile.link == LinkTypes.LINK:
        # link
        ret, err = inst.install(templ, dotfile.src, dotfile.dst,
                                dotfile.link,
                                actionexec=pre_actions_exec,
                                is_template=is_template,
                                ignore=ignores,
                                chmod=dotfile.chmod,
                                force_chmod=opts.install_force_chmod)
    elif hasattr(dotfile, 'link') and \
            dotfile.link == LinkTypes.LINK_CHILDREN:
        # link_children
        ret, err = inst.install(templ, dotfile.src, dotfile.dst,
                                dotfile.link,
                                actionexec=pre_actions_exec,
                                is_template=is_template,
                                chmod=dotfile.chmod,
                                ignore=ignores,
                                force_chmod=opts.install_force_chmod)
    else:
        # nolink
        src = dotfile.src
        tmp = None
        if dotfile.trans_r:
            tmp = apply_trans(opts.dotpath, dotfile, templ, debug=opts.debug)
            if not tmp:
                return False, dotfile.key, None
            src = tmp
        # make sure to re-evaluate if is template
        is_template = dotfile.template and Templategen.is_template(
            src,
            ignore=ignores,
        )
        ret, err = inst.install(templ, src, dotfile.dst,
                                LinkTypes.NOLINK,
                                actionexec=pre_actions_exec,
                                noempty=dotfile.noempty,
                                ignore=ignores,
                                is_template=is_template,
                                chmod=dotfile.chmod,
                                force_chmod=opts.install_force_chmod)
        if tmp:
            tmp = os.path.join(opts.dotpath, tmp)
            if os.path.exists(tmp):
                removepath(tmp, LOG)

    # check result of installation
    if ret:
        # dotfile was installed
        if not opts.install_temporary:
            defactions = opts.install_default_actions_post
            postactions = dotfile.get_post_actions()
            post_actions_exec = action_executor(opts, postactions, defactions,
                                                templ, post=True)
            post_actions_exec()
    else:
        # dotfile was NOT installed
        if opts.install_force_action:
            # pre-actions
            LOG.dbg('force pre action execution ...')
            pre_actions_exec()
            # post-actions
            LOG.dbg('force post action execution ...')
            defactions = opts.install_default_actions_post
            postactions = dotfile.get_post_actions()
            post_actions_exec = action_executor(opts, postactions, defactions,
                                                templ, post=True)
            post_actions_exec()

    return ret, dotfile.key, err


def cmd_install(opts):
    """install dotfiles for this profile"""
    dotfiles = opts.dotfiles
    prof = opts.conf.get_profile()

    adapt_workers(opts, LOG)

    pro_pre_actions = prof.get_pre_actions() if prof else []
    pro_post_actions = prof.get_post_actions() if prof else []

    if opts.install_keys:
        # filtered dotfiles to install
        uniq = uniq_list(opts.install_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
    if not dotfiles:
        msg = 'no dotfile to install for this profile (\"{}\")'
        LOG.warn(msg.format(opts.profile))
        return False

    # the installer
    tmpdir = None
    if opts.install_temporary:
        tmpdir = get_tmpdir()

    installed = []

    # execute profile pre-action
    LOG.dbg('run {} profile pre actions'.format(len(pro_pre_actions)))
    templ = _get_templater(opts)
    ret, _ = action_executor(opts, pro_pre_actions, [], templ, post=False)()
    if not ret:
        return False

    # install each dotfile
    if opts.workers > 1:
        # in parallel
        LOG.dbg('run with {} workers'.format(opts.workers))
        ex = futures.ThreadPoolExecutor(max_workers=opts.workers)

        wait_for = []
        for dotfile in dotfiles:
            j = ex.submit(_dotfile_install, opts, dotfile, tmpdir=tmpdir)
            wait_for.append(j)
        # check result
        for fut in futures.as_completed(wait_for):
            tmpret, key, err = fut.result()
            # check result
            if tmpret:
                installed.append(key)
            elif err:
                LOG.err('installing \"{}\" failed: {}'.format(key,
                                                              err))
    else:
        # sequentially
        for dotfile in dotfiles:
            tmpret, key, err = _dotfile_install(opts, dotfile, tmpdir=tmpdir)
            # check result
            if tmpret:
                installed.append(key)
            elif err:
                LOG.err('installing \"{}\" failed: {}'.format(key,
                                                              err))

    # execute profile post-action
    if len(installed) > 0 or opts.install_force_action:
        msg = 'run {} profile post actions'
        LOG.dbg(msg.format(len(pro_post_actions)))
        ret, _ = action_executor(opts, pro_post_actions,
                                 [], templ, post=False)()
        if not ret:
            return False

    LOG.dbg('install done: installed \"{}\"'.format(','.join(installed)))

    if opts.install_temporary:
        LOG.log('\ninstalled to tmp \"{}\".'.format(tmpdir))
    LOG.log('\n{} dotfile(s) installed.'.format(len(installed)))
    return True


def _workdir_enum(opts):
    workdir_files = []
    for root, dirs, files in os.walk(opts.workdir):
        for file in files:
            fpath = os.path.join(root, file)
            workdir_files.append(fpath)

    for dotfile in opts.dotfiles:
        src = os.path.join(opts.dotpath, dotfile.src)
        if dotfile.link == LinkTypes.NOLINK:
            # ignore not link files
            continue
        if not Templategen.is_template(src):
            # ignore not template
            continue
        newpath = pivot_path(dotfile.dst, opts.workdir,
                             striphome=True, logger=None)
        if os.path.isdir(newpath):
            # recursive
            pattern = '{}/*'.format(newpath)
            files = workdir_files.copy()
            for f in files:
                if fnmatch.fnmatch(f, pattern):
                    workdir_files.remove(f)
            # only checks children
            children = [f.path for f in os.scandir(newpath)]
            for c in children:
                if c in workdir_files:
                    workdir_files.remove(c)
        else:
            if newpath in workdir_files:
                workdir_files.remove(newpath)
    for w in workdir_files:
        line = '=> \"{}\" does not exist in dotdrop'
        LOG.log(line.format(w))
    return len(workdir_files)


def cmd_compare(opts, tmp):
    """compare dotfiles and return True if all identical"""
    dotfiles = opts.dotfiles
    if not dotfiles:
        msg = 'no dotfile defined for this profile (\"{}\")'
        LOG.warn(msg.format(opts.profile))
        return True

    # compare only specific files
    selected = dotfiles
    if opts.compare_focus:
        selected = _select(opts.compare_focus, dotfiles)

    if len(selected) < 1:
        LOG.log('\nno dotfile to compare')
        return False

    same = True
    cnt = 0
    if opts.workers > 1:
        # in parallel
        LOG.dbg('run with {} workers'.format(opts.workers))
        ex = futures.ThreadPoolExecutor(max_workers=opts.workers)
        wait_for = []
        for dotfile in selected:
            if not dotfile.src and not dotfile.dst:
                # ignore fake dotfile
                continue
            j = ex.submit(_dotfile_compare, opts, dotfile, tmp)
            wait_for.append(j)
        # check result
        for fut in futures.as_completed(wait_for):
            if not fut.result():
                same = False
            cnt += 1
    else:
        # sequentially
        for dotfile in selected:
            if not dotfile.src and not dotfile.dst:
                # ignore fake dotfile
                continue
            if not _dotfile_compare(opts, dotfile, tmp):
                same = False
            cnt += 1

    # TODO
    if  _workdir_enum(opts) > 0:
        same = False

    LOG.log('\n{} dotfile(s) compared.'.format(cnt))
    return same


def cmd_update(opts):
    """update the dotfile(s) from path(s) or key(s)"""
    cnt = 0
    paths = opts.update_path
    iskey = opts.update_iskey

    if opts.profile not in [p.key for p in opts.profiles]:
        LOG.err('no such profile \"{}\"'.format(opts.profile))
        return False

    adapt_workers(opts, LOG)

    if not paths:
        # update the entire profile
        if iskey:
            LOG.dbg('update by keys: {}'.format(paths))
            paths = [d.key for d in opts.dotfiles]
        else:
            LOG.dbg('update by paths: {}'.format(paths))
            paths = [d.dst for d in opts.dotfiles]
        msg = 'Update all dotfiles for profile \"{}\"'.format(opts.profile)
        if opts.safe and not LOG.ask(msg):
            LOG.log('\n{} file(s) updated.'.format(cnt))
            return False

    # check there's something to do
    if not paths:
        LOG.log('\nno dotfile to update')
        return True

    LOG.dbg('dotfile to update: {}'.format(paths))

    # update each dotfile
    if opts.workers > 1:
        # in parallel
        LOG.dbg('run with {} workers'.format(opts.workers))
        ex = futures.ThreadPoolExecutor(max_workers=opts.workers)
        wait_for = []
        for path in paths:
            j = ex.submit(_dotfile_update, opts, path, key=iskey)
            wait_for.append(j)
        # check result
        for fut in futures.as_completed(wait_for):
            if fut.result():
                cnt += 1
    else:
        # sequentially
        for path in paths:
            if _dotfile_update(opts, path, key=iskey):
                cnt += 1

    LOG.log('\n{} file(s) updated.'.format(cnt))
    return cnt == len(paths)


def cmd_importer(opts):
    """import dotfile(s) from paths"""
    ret = True
    cnt = 0
    paths = opts.import_path
    importer = Importer(opts.profile, opts.conf,
                        opts.dotpath, opts.diff_command,
                        dry=opts.dry, safe=opts.safe,
                        debug=opts.debug,
                        keepdot=opts.keepdot,
                        ignore=opts.import_ignore)

    for path in paths:
        tmpret = importer.import_path(path, import_as=opts.import_as,
                                      import_link=opts.import_link,
                                      import_mode=opts.import_mode)
        if tmpret < 0:
            ret = False
        elif tmpret > 0:
            cnt += 1

    if opts.dry:
        LOG.dry('new config file would be:')
        LOG.raw(opts.conf.dump())
    else:
        opts.conf.save()
    LOG.log('\n{} file(s) imported.'.format(cnt))

    return ret


def cmd_list_profiles(opts):
    """list all profiles"""
    LOG.emph('Available profile(s):\n')
    for profile in opts.profiles:
        if opts.profiles_grepable:
            fmt = '{}'.format(profile.key)
            LOG.raw(fmt)
        else:
            LOG.sub(profile.key, end='')
            LOG.log(' ({} dotfiles)'.format(len(profile.dotfiles)))
    LOG.log('')


def cmd_files(opts):
    """list all dotfiles for a specific profile"""
    if opts.profile not in [p.key for p in opts.profiles]:
        LOG.warn('unknown profile \"{}\"'.format(opts.profile))
        return
    what = 'Dotfile(s)'
    if opts.files_templateonly:
        what = 'Template(s)'
    LOG.emph('{} for profile \"{}\":\n'.format(what, opts.profile))
    for dotfile in opts.dotfiles:
        if opts.files_templateonly:
            src = os.path.join(opts.dotpath, dotfile.src)
            if not Templategen.is_template(src):
                continue
        if opts.files_grepable:
            fmt = '{},dst:{},src:{},link:{}'
            fmt = fmt.format(dotfile.key, dotfile.dst,
                             dotfile.src, dotfile.link.name.lower())
            if dotfile.chmod:
                fmt += ',chmod:{:o}'
            else:
                fmt += ',chmod:None'
            LOG.raw(fmt)
        else:
            LOG.log('{}'.format(dotfile.key), bold=True)
            LOG.sub('dst: {}'.format(dotfile.dst))
            LOG.sub('src: {}'.format(dotfile.src))
            LOG.sub('link: {}'.format(dotfile.link.name.lower()))
            if dotfile.chmod:
                LOG.sub('chmod: {:o}'.format(dotfile.chmod))
    LOG.log('')


def cmd_detail(opts):
    """list details on all files for all dotfile entries"""
    if opts.profile not in [p.key for p in opts.profiles]:
        LOG.warn('unknown profile \"{}\"'.format(opts.profile))
        return
    dotfiles = opts.dotfiles
    if opts.detail_keys:
        # filtered dotfiles to install
        uniq = uniq_list(opts.details_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
    LOG.emph('dotfiles details for profile \"{}\":\n'.format(opts.profile))
    for dotfile in dotfiles:
        _detail(opts.dotpath, dotfile)
    LOG.log('')


def cmd_remove(opts):
    """remove dotfile from dotpath and from config"""
    paths = opts.remove_path
    iskey = opts.remove_iskey

    if not paths:
        LOG.log('no dotfile to remove')
        return False
    LOG.dbg('dotfile(s) to remove: {}'.format(','.join(paths)))

    removed = []
    for key in paths:
        if not iskey:
            # by path
            dotfiles = opts.conf.get_dotfile_by_dst(key)
            if not dotfiles:
                LOG.warn('{} ignored, does not exist'.format(key))
                continue
        else:
            # by key
            dotfile = opts.conf.get_dotfile(key)
            if not dotfile:
                LOG.warn('{} ignored, does not exist'.format(key))
                continue
            dotfiles = [dotfile]

        for dotfile in dotfiles:
            k = dotfile.key
            # ignore if uses any type of link
            if dotfile.link != LinkTypes.NOLINK:
                msg = '{} uses link/link_children, remove manually'
                LOG.warn(msg.format(k))
                continue

            LOG.dbg('removing {}'.format(key))

            # make sure is part of the profile
            if dotfile.key not in [d.key for d in opts.dotfiles]:
                msg = '{} ignored, not associated to this profile'
                LOG.warn(msg.format(key))
                continue
            profiles = opts.conf.get_profiles_by_dotfile_key(k)
            pkeys = ','.join([p.key for p in profiles])
            if opts.dry:
                LOG.dry('would remove {} from {}'.format(dotfile, pkeys))
                continue
            msg = 'Remove \"{}\" from all these profiles: {}'.format(k, pkeys)
            if opts.safe and not LOG.ask(msg):
                return False
            LOG.dbg('remove dotfile: {}'.format(dotfile))

            for profile in profiles:
                if not opts.conf.del_dotfile_from_profile(dotfile, profile):
                    return False
            if not opts.conf.del_dotfile(dotfile):
                return False

            # remove dotfile from dotpath
            dtpath = os.path.join(opts.dotpath, dotfile.src)
            removepath(dtpath, LOG)
            # remove empty directory
            parent = os.path.dirname(dtpath)
            # remove any empty parent up to dotpath
            while parent != opts.dotpath:
                if os.path.isdir(parent) and not os.listdir(parent):
                    msg = 'Remove empty dir \"{}\"'.format(parent)
                    if opts.safe and not LOG.ask(msg):
                        break
                    removepath(parent, LOG)
                parent = os.path.dirname(parent)
            removed.append(dotfile)

    if opts.dry:
        LOG.dry('new config file would be:')
        LOG.raw(opts.conf.dump())
    else:
        opts.conf.save()
    if removed:
        LOG.log('\nFollowing dotfile(s) are not tracked anymore:')
        entries = ['- \"{}\" (was tracked as \"{}\")'.format(r.dst, r.key)
                   for r in removed]
        LOG.log('\n'.join(entries))
    else:
        LOG.log('\nno dotfile removed')
    return True


###########################################################
# helpers
###########################################################


def _get_install_installer(opts, tmpdir=None):
    """get an installer instance for cmd_install"""
    inst = Installer(create=opts.create, backup=opts.backup,
                     dry=opts.dry, safe=opts.safe,
                     base=opts.dotpath, workdir=opts.workdir,
                     diff=opts.install_diff, debug=opts.debug,
                     totemp=tmpdir,
                     showdiff=opts.install_showdiff,
                     backup_suffix=opts.install_backup_suffix,
                     diff_cmd=opts.diff_command)
    return inst


def _get_templater(opts):
    """get an templater instance"""
    templ = Templategen(base=opts.dotpath, variables=opts.variables,
                        func_file=opts.func_file, filter_file=opts.filter_file,
                        debug=opts.debug)
    return templ


def _detail(dotpath, dotfile):
    """display details on all files under a dotfile entry"""
    entry = '{}'.format(dotfile.key)
    attribs = []
    attribs.append('dst: \"{}\"'.format(dotfile.dst))
    attribs.append('link: \"{}\"'.format(dotfile.link.name.lower()))
    attribs.append('chmod: \"{}\"'.format(dotfile.chmod))
    LOG.log('{} ({})'.format(entry, ', '.join(attribs)))
    path = os.path.join(dotpath, os.path.expanduser(dotfile.src))
    if not os.path.isdir(path):
        template = 'no'
        if dotfile.template and Templategen.is_template(path):
            template = 'yes'
        LOG.sub('{} (template:{})'.format(path, template))
    else:
        for root, _, files in os.walk(path):
            for file in files:
                fpath = os.path.join(root, file)
                template = 'no'
                if dotfile.template and Templategen.is_template(fpath):
                    template = 'yes'
                LOG.sub('{} (template:{})'.format(fpath, template))


def _select(selections, dotfiles):
    selected = []
    for selection in selections:
        dotfile = next(
            (x for x in dotfiles
                if os.path.expanduser(x.dst) == os.path.expanduser(selection)),
            None
        )
        if dotfile:
            selected.append(dotfile)
        else:
            LOG.err('no dotfile matches \"{}\"'.format(selection))
    return selected


def apply_trans(dotpath, dotfile, templater, debug=False):
    """
    apply the read transformation to the dotfile
    return None if fails and new source if succeed
    """
    src = dotfile.src
    new_src = '{}.{}'.format(src, TRANS_SUFFIX)
    trans = dotfile.trans_r
    LOG.dbg('executing transformation: {}'.format(trans))
    srcpath = os.path.join(dotpath, src)
    temp = os.path.join(dotpath, new_src)
    if not trans.transform(srcpath, temp, templater=templater, debug=debug):
        msg = 'transformation \"{}\" failed for {}'
        LOG.err(msg.format(trans.key, dotfile.key))
        if new_src and os.path.exists(new_src):
            removepath(new_src, LOG)
        return None
    return new_src


###########################################################
# main
###########################################################

def _exec_command(opts):
    """execute command"""
    ret = True
    command = ''
    try:

        if opts.cmd_profiles:
            # list existing profiles
            command = 'profiles'
            LOG.dbg('running cmd: {}'.format(command))
            cmd_list_profiles(opts)

        elif opts.cmd_files:
            # list files for selected profile
            command = 'files'
            LOG.dbg('running cmd: {}'.format(command))
            cmd_files(opts)

        elif opts.cmd_install:
            # install the dotfiles stored in dotdrop
            command = 'install'
            LOG.dbg('running cmd: {}'.format(command))
            ret = cmd_install(opts)

        elif opts.cmd_compare:
            # compare local dotfiles with dotfiles stored in dotdrop
            command = 'compare'
            LOG.dbg('running cmd: {}'.format(command))
            tmp = get_tmpdir()
            ret = cmd_compare(opts, tmp)
            # clean tmp directory
            removepath(tmp, LOG)

        elif opts.cmd_import:
            # import dotfile(s)
            command = 'import'
            LOG.dbg('running cmd: {}'.format(command))
            ret = cmd_importer(opts)

        elif opts.cmd_update:
            # update a dotfile
            command = 'update'
            LOG.dbg('running cmd: {}'.format(command))
            ret = cmd_update(opts)

        elif opts.cmd_detail:
            # detail files
            command = 'detail'
            LOG.dbg('running cmd: {}'.format(command))
            cmd_detail(opts)

        elif opts.cmd_remove:
            # remove dotfile
            command = 'remove'
            LOG.dbg('running cmd: {}'.format(command))
            cmd_remove(opts)

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False

    return ret, command


def main():
    """entry point"""
    # check dependencies are met
    try:
        dependencies_met()
    except UnmetDependency as exc:
        LOG.err(exc)
        return False

    time0 = time.time()
    try:
        opts = Options()
    except YamlException as exc:
        LOG.err('config error: {}'.format(str(exc)))
        return False
    except UndefinedException as exc:
        LOG.err('config error: {}'.format(str(exc)))
        return False

    if opts.debug:
        LOG.debug = opts.debug
        LOG.dbg('\n\n')
    options_time = time.time() - time0

    if opts.check_version:
        check_version()

    time0 = time.time()
    ret, command = _exec_command(opts)
    cmd_time = time.time() - time0

    LOG.dbg('done executing command \"{}\"'.format(command))
    LOG.dbg('options loaded in {}'.format(options_time))
    LOG.dbg('command executed in {}'.format(cmd_time))

    if ret and opts.conf.save():
        LOG.log('config file updated')

    LOG.dbg('return {}'.format(ret))
    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
