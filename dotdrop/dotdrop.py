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
from dotdrop.uninstaller import Uninstaller
from dotdrop.updater import Updater
from dotdrop.comparator import Comparator
from dotdrop.importer import Importer
from dotdrop.utils import get_tmpdir, removepath, \
    uniq_list, ignores_to_absolute, dependencies_met, \
    adapt_workers, check_version, pivot_path, dir_empty
from dotdrop.linktypes import LinkTypes
from dotdrop.exceptions import YamlException, \
    UndefinedException, UnmetDependency, \
    ConfigException, OptionsException

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
                LOG.dry(f'would execute def-{actiontype}-action: {action}')
                continue
            LOG.dbg(f'executing def-{actiontype}-action: {action}')
            ret = action.execute(templater=templater, debug=opts.debug)
            if not ret:
                err = f'def-{actiontype}-action \"{action.key}\" failed'
                LOG.err(err)
                return False, err

        # execute actions
        for action in actions:
            if opts.dry:
                err = f'would execute {actiontype}-action: {action}'
                LOG.dry(err)
                continue
            LOG.dbg(f'executing {actiontype}-action: {action}')
            ret = action.execute(templater=templater, debug=opts.debug)
            if not ret:
                err = f'{actiontype}-action \"{action.key}\" failed'
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
                     diff_cmd=opts.diff_command,
                     force_chmod=True)
    comp = Comparator(diff_cmd=opts.diff_command, debug=opts.debug,
                      ignore_missing_in_dotdrop=ignore_missing_in_dotdrop)

    # add dotfile variables
    newvars = dotfile.get_dotfile_variables()
    templ.add_tmp_vars(newvars=newvars)

    # dotfiles does not exist / not installed
    LOG.dbg(f'comparing {dotfile}')

    src = dotfile.src
    if not os.path.lexists(os.path.expanduser(dotfile.dst)):
        line = f'=> compare {dotfile.key}: \"{dotfile.dst}\" '
        line += 'does not exist on destination'
        LOG.log(line)
        return False

    # apply transformation
    tmpsrc = None
    if dotfile.trans_install:
        LOG.dbg('applying transformation before comparing')
        tmpsrc = apply_install_trans(opts.dotpath, dotfile,
                                     templ, debug=opts.debug)
        if not tmpsrc:
            # could not apply trans
            return False
        src = tmpsrc

    # is a symlink pointing to itself
    asrc = os.path.join(opts.dotpath, os.path.expanduser(src))
    adst = os.path.expanduser(dotfile.dst)
    if os.path.samefile(asrc, adst):
        line = f'=> compare {dotfile.key}: diffing with \"{dotfile.dst}\"'
        LOG.dbg(line)
        LOG.dbg('points to itself')
        return True

    ignores = list(set(opts.compare_ignore + dotfile.cmpignore))
    ignores = ignores_to_absolute(ignores, [dotfile.dst, dotfile.src],
                                  debug=opts.debug)

    insttmp = None
    if dotfile.template and \
        Templategen.path_is_template(src,
                                     debug=opts.debug):
        # install dotfile to temporary dir for compare
        ret, err, insttmp = inst.install_to_temp(templ, tmp, src, dotfile.dst,
                                                 is_template=True,
                                                 chmod=dotfile.chmod,
                                                 set_create=True)
        if not ret:
            # failed to install to tmp
            line = f'=> compare {dotfile.key} error: {err}'
            LOG.log(line)
            LOG.err(err)
            return False
        src = insttmp

    # compare
    # need to be executed before cleaning
    diff = comp.compare(src, dotfile.dst, ignore=ignores, mode=dotfile.chmod)

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
            line = f'=> differ: \"{dotfile.key}\" \"{dotfile.dst}\"'
            LOG.log(line)
        else:
            line = f'=> compare {dotfile.key}: diffing with \"{dotfile.dst}\"'
            LOG.log(line)
            LOG.emph(diff)
        return False

    # no difference
    line = f'=> compare {dotfile.key}: diffing with \"{dotfile.dst}\"'
    LOG.dbg(line)
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

    LOG.dbg(f'installing dotfile: \"{dotfile.key}\"')
    LOG.dbg(dotfile.prt())

    ignores = list(set(opts.install_ignore + dotfile.instignore))
    ignores = ignores_to_absolute(ignores, [dotfile.dst, dotfile.src],
                                  debug=opts.debug)

    is_template = dotfile.template and Templategen.path_is_template(
        dotfile.src,
    )
    if hasattr(dotfile, 'link') and dotfile.link in (
        LinkTypes.LINK, LinkTypes.LINK_CHILDREN,
        LinkTypes.RELATIVE, LinkTypes.ABSOLUTE
    ):
        # nolink|relative|absolute|link_children
        ret, err = inst.install(templ, dotfile.src, dotfile.dst,
                                dotfile.link,
                                actionexec=pre_actions_exec,
                                is_template=is_template,
                                ignore=ignores,
                                chmod=dotfile.chmod)
    else:
        # nolink
        src = dotfile.src
        tmp = None
        if dotfile.trans_install:
            tmp = apply_install_trans(opts.dotpath, dotfile,
                                      templ, debug=opts.debug)
            if not tmp:
                return False, dotfile.key, None
            src = tmp
        # make sure to re-evaluate if is template
        is_template = dotfile.template and Templategen.path_is_template(src)
        ret, err = inst.install(templ, src, dotfile.dst,
                                LinkTypes.NOLINK,
                                actionexec=pre_actions_exec,
                                noempty=dotfile.noempty,
                                ignore=ignores,
                                is_template=is_template,
                                chmod=dotfile.chmod)
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
        msg = f'no dotfile to install for this profile (\"{opts.profile}\")'
        LOG.warn(msg)
        return False

    lfs = [k.key for k in dotfiles]
    LOG.dbg(f'dotfiles registered for install: {lfs}')

    # the installer
    tmpdir = None
    if opts.install_temporary:
        tmpdir = get_tmpdir()

    installed = []

    # clear the workdir
    if opts.install_clear_workdir and not opts.dry:
        LOG.dbg(f'clearing the workdir under {opts.workdir}')
        for root, _, files in os.walk(opts.workdir):
            for file in files:
                fpath = os.path.join(root, file)
                removepath(fpath, logger=LOG)

    # execute profile pre-action
    LOG.dbg(f'run {len(pro_pre_actions)} profile pre actions')
    templ = _get_templater(opts)
    ret, _ = action_executor(opts, pro_pre_actions, [], templ, post=False)()
    if not ret:
        return False

    # install each dotfile
    if opts.workers > 1:
        # in parallel
        LOG.dbg(f'run with {opts.workers} workers')
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
                LOG.err(f'installing \"{key}\" failed: {err}')
    else:
        # sequentially
        for dotfile in dotfiles:
            tmpret, key, err = _dotfile_install(opts, dotfile, tmpdir=tmpdir)
            # check result
            if tmpret:
                installed.append(key)
            elif err:
                LOG.err(f'installing \"{key}\" failed: {err}')

    # execute profile post-action
    if len(installed) > 0 or opts.install_force_action:
        msg = f'run {len(pro_post_actions)} profile post actions'
        LOG.dbg(msg)
        ret, _ = action_executor(opts, pro_post_actions,
                                 [], templ, post=False)()
        if not ret:
            return False

    insts = ','.join(installed)
    LOG.dbg(f'install done: installed \"{insts}\"')

    if opts.install_temporary:
        LOG.log(f'\ninstalled to tmp \"{tmpdir}\".')
    LOG.log(f'\n{len(installed)} dotfile(s) installed.')
    return True


def _workdir_enum(opts):
    workdir_files = []
    for root, _, files in os.walk(opts.workdir):
        for file in files:
            fpath = os.path.join(root, file)
            workdir_files.append(fpath)

    for dotfile in opts.dotfiles:
        src = os.path.join(opts.dotpath, dotfile.src)
        if dotfile.link == LinkTypes.NOLINK:
            # ignore not link files
            continue
        if not Templategen.path_is_template(src):
            # ignore not template
            continue
        newpath = pivot_path(dotfile.dst, opts.workdir,
                             striphome=True, logger=None)
        if os.path.isdir(newpath):
            # recursive
            pattern = f'{newpath}/*'
            files = workdir_files.copy()
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    workdir_files.remove(file)
            # only checks children
            children = [f.path for f in os.scandir(newpath)]
            for child in children:
                if child in workdir_files:
                    workdir_files.remove(child)
        else:
            if newpath in workdir_files:
                workdir_files.remove(newpath)
    for wfile in workdir_files:
        line = f'=> \"{wfile}\" does not exist in dotdrop'
        LOG.log(line)
    return len(workdir_files)


def cmd_compare(opts, tmp):
    """compare dotfiles and return True if all identical"""
    dotfiles = opts.dotfiles
    if not dotfiles:
        msg = f'no dotfile defined for this profile (\"{opts.profile}\")'
        LOG.warn(msg)
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
        LOG.dbg(f'run with {opts.workers} workers')
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

    if opts.compare_workdir and _workdir_enum(opts) > 0:
        same = False

    LOG.log(f'\n{cnt} dotfile(s) compared.')
    return same


def cmd_update(opts):
    """update the dotfile(s) from path(s) or key(s)"""
    cnt = 0
    paths = opts.update_path
    iskey = opts.update_iskey

    if opts.profile not in [p.key for p in opts.profiles]:
        LOG.err(f'no such profile \"{opts.profile}\"')
        return False

    adapt_workers(opts, LOG)

    if not paths:
        # update the entire profile
        if iskey:
            LOG.dbg(f'update by keys: {paths}')
            paths = [d.key for d in opts.dotfiles]
        else:
            LOG.dbg(f'update by paths: {paths}')
            paths = [d.dst for d in opts.dotfiles]
        msg = f'Update all dotfiles for profile \"{opts.profile}\"'
        if opts.safe and not LOG.ask(msg):
            LOG.log(f'\n{cnt} file(s) updated.')
            return False

    # check there's something to do
    if not paths:
        LOG.log('\nno dotfile to update')
        return True

    LOG.dbg(f'dotfile to update: {paths}')

    # update each dotfile
    if opts.workers > 1:
        # in parallel
        LOG.dbg(f'run with {opts.workers} workers')
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

    LOG.log(f'\n{cnt} file(s) updated.')
    return cnt == len(paths)


def cmd_importer(opts):
    """import dotfile(s) from paths"""
    ret = True
    cnt = 0
    paths = opts.import_path
    importer = Importer(opts.profile, opts.conf,
                        opts.dotpath, opts.diff_command,
                        opts.variables,
                        dry=opts.dry, safe=opts.safe,
                        debug=opts.debug,
                        keepdot=opts.keepdot,
                        ignore=opts.import_ignore)

    for path in paths:
        tmpret = importer.import_path(path,
                                      import_as=opts.import_as,
                                      import_link=opts.import_link,
                                      import_mode=opts.import_mode,
                                      trans_install=opts.import_trans_install,
                                      trans_update=opts.import_trans_update)
        if tmpret < 0:
            ret = False
        elif tmpret > 0:
            cnt += 1

    if opts.dry:
        LOG.dry('new config file would be:')
        LOG.raw(opts.conf.dump())
    else:
        opts.conf.save()
    LOG.log(f'\n{cnt} file(s) imported.')

    return ret


def cmd_list_profiles(opts):
    """list all profiles"""
    LOG.emph('Available profile(s):\n')
    for profile in opts.profiles:
        if opts.profiles_grepable:
            fmt = f'{profile.key}'
            LOG.raw(fmt)
        else:
            LOG.sub(profile.key, end='')
            LOG.log(f' ({len(profile.dotfiles)} dotfiles)')
    LOG.log('')


def cmd_files(opts):
    """list all dotfiles for a specific profile"""
    if opts.profile not in [p.key for p in opts.profiles]:
        LOG.warn(f'unknown profile \"{opts.profile}\"')
        return
    what = 'Dotfile(s)'
    if opts.files_templateonly:
        what = 'Template(s)'
    LOG.emph(f'{what} for profile \"{opts.profile}\":\n')
    for dotfile in opts.dotfiles:
        if opts.files_templateonly:
            src = os.path.join(opts.dotpath, dotfile.src)
            if not Templategen.path_is_template(src):
                continue
        if opts.files_grepable:
            fmt = f'{dotfile.key},'
            fmt += f'dst:{dotfile.dst},'
            fmt += f'src:{dotfile.src},'
            fmt += f'link:{dotfile.link.name.lower()}'
            if dotfile.chmod:
                fmt += f',chmod:{dotfile.chmod:o}'
            else:
                fmt += ',chmod:None'
            LOG.raw(fmt)
        else:
            LOG.log(f'{dotfile.key}', bold=True)
            LOG.sub(f'dst: {dotfile.dst}')
            LOG.sub(f'src: {dotfile.src}')
            LOG.sub(f'link: {dotfile.link.name.lower()}')
            if dotfile.chmod:
                LOG.sub(f'chmod: {dotfile.chmod:o}')
    LOG.log('')


def cmd_detail(opts):
    """list details on all files for all dotfile entries"""
    if opts.profile not in [p.key for p in opts.profiles]:
        LOG.warn(f'unknown profile \"{opts.profile}\"')
        return
    dotfiles = opts.dotfiles
    if opts.detail_keys:
        # filtered dotfiles to install
        uniq = uniq_list(opts.detail_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
    LOG.emph(f'dotfiles details for profile \"{opts.profile}\":\n')
    for dotfile in dotfiles:
        _detail(opts.dotpath, dotfile)
    LOG.log('')


def cmd_uninstall(opts):
    """uninstall"""
    dotfiles = opts.dotfiles
    keys = opts.uninstall_key

    if keys:
        # uninstall only specific keys for this profile
        dotfiles = []
        for key in uniq_list(keys):
            dotfile = opts.conf.get_dotfile(key)
            if dotfile:
                dotfiles.append(dotfile)

    if not dotfiles:
        msg = f'no dotfile to uninstall for this profile (\"{opts.profile}\")'
        LOG.warn(msg)
        return False

    if opts.debug:
        lfs = [k.key for k in dotfiles]
        LOG.dbg(f'dotfiles registered for uninstall: {lfs}')

    uninst = Uninstaller(base=opts.dotpath,
                         workdir=opts.workdir,
                         dry=opts.dry,
                         safe=opts.safe,
                         debug=opts.debug,
                         backup_suffix=opts.install_backup_suffix)
    uninstalled = 0
    for dotf in dotfiles:
        res, msg = uninst.uninstall(dotf.src,
                                    dotf.dst,
                                    dotf.link)
        if not res:
            LOG.err(msg)
            continue
        uninstalled += 1
    LOG.log(f'\n{uninstalled} dotfile(s) uninstalled.')
    return True


def cmd_remove(opts):
    """remove dotfile from dotpath and from config"""
    paths = opts.remove_path
    iskey = opts.remove_iskey

    if not paths:
        LOG.log('no dotfile to remove')
        return False
    pathss = ','.join(paths)
    LOG.dbg(f'dotfile(s) to remove: {pathss}')

    removed = []
    for key in paths:
        if not iskey:
            # by path
            dotfiles = opts.conf.get_dotfile_by_dst(key)
            if not dotfiles:
                LOG.warn(f'{key} ignored, does not exist')
                continue
        else:
            # by key
            dotfile = opts.conf.get_dotfile(key)
            if not dotfile:
                LOG.warn(f'{key} ignored, does not exist')
                continue
            dotfiles = [dotfile]

        for dotfile in dotfiles:
            k = dotfile.key
            # ignore if uses any type of link
            if dotfile.link != LinkTypes.NOLINK:
                msg = f'{k} uses symlink, remove manually'
                LOG.warn(msg)
                continue

            LOG.dbg(f'removing {key}')

            # make sure is part of the profile
            if dotfile.key not in [d.key for d in opts.dotfiles]:
                msg = f'{key} ignored, not associated to this profile'
                LOG.warn(msg)
                continue
            profiles = opts.conf.get_profiles_by_dotfile_key(k)
            pkeys = ','.join([p.key for p in profiles])
            if opts.dry:
                LOG.dry(f'would remove {dotfile} from {pkeys}')
                continue
            msg = f'Remove \"{k}\" from all these profiles: {pkeys}'
            if opts.safe and not LOG.ask(msg):
                return False
            LOG.dbg(f'remove dotfile: {dotfile}')

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
                if os.path.isdir(parent) and dir_empty(parent):
                    msg = f'Remove empty dir \"{parent}\"'
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
        entries = [f'- \"{r.dst}\" (was tracked as \"{r.key}\")'
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
                     diff_cmd=opts.diff_command,
                     remove_existing_in_dir=opts.install_remove_existing,
                     force_chmod=opts.install_force_chmod)
    return inst


def _get_templater(opts):
    """get an templater instance"""
    templ = Templategen(base=opts.dotpath, variables=opts.variables,
                        func_file=opts.func_file, filter_file=opts.filter_file,
                        debug=opts.debug)
    return templ


def _detail(dotpath, dotfile):
    """display details on all files under a dotfile entry"""
    entry = f'{dotfile.key}'
    attribs = []
    attribs.append(f'dst: \"{dotfile.dst}\"')
    attribs.append(f'link: \"{dotfile.link.name.lower()}\"')
    attribs.append(f'chmod: \"{dotfile.chmod}\"')
    attrs = ', '.join(attribs)
    LOG.log(f'{entry} ({attrs})')
    path = os.path.join(dotpath, os.path.expanduser(dotfile.src))
    if not os.path.isdir(path):
        template = 'no'
        if dotfile.template and Templategen.path_is_template(path):
            template = 'yes'
        LOG.sub(f'{path} (template:{template})')
    else:
        for root, _, files in os.walk(path):
            for file in files:
                fpath = os.path.join(root, file)
                template = 'no'
                if dotfile.template and Templategen.path_is_template(fpath):
                    template = 'yes'
                LOG.sub(f'{fpath} (template:{template})')


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
            LOG.err(f'no dotfile matches \"{selection}\"')
    return selected


def apply_install_trans(dotpath, dotfile, templater, debug=False):
    """
    apply the install transformation to the dotfile
    return None if fails and new source if succeed
    """
    src = dotfile.src
    new_src = f'{src}.{TRANS_SUFFIX}'
    trans = dotfile.trans_install
    LOG.dbg(f'executing install transformation: {trans}')
    srcpath = os.path.join(dotpath, src)
    temp = os.path.join(dotpath, new_src)
    if not trans.transform(srcpath, temp, templater=templater, debug=debug):
        msg = f'install transformation \"{trans.key}\"'
        msg += f'failed for {dotfile.key}'
        LOG.err(msg)
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
            LOG.dbg(f'running cmd: {command}')
            cmd_list_profiles(opts)

        elif opts.cmd_files:
            # list files for selected profile
            command = 'files'
            LOG.dbg(f'running cmd: {command}')
            cmd_files(opts)

        elif opts.cmd_install:
            # install the dotfiles stored in dotdrop
            command = 'install'
            LOG.dbg(f'running cmd: {command}')
            ret = cmd_install(opts)

        elif opts.cmd_compare:
            # compare local dotfiles with dotfiles stored in dotdrop
            command = 'compare'
            LOG.dbg(f'running cmd: {command}')
            tmp = get_tmpdir()
            ret = cmd_compare(opts, tmp)
            # clean tmp directory
            removepath(tmp, LOG)

        elif opts.cmd_import:
            # import dotfile(s)
            command = 'import'
            LOG.dbg(f'running cmd: {command}')
            ret = cmd_importer(opts)

        elif opts.cmd_update:
            # update a dotfile
            command = 'update'
            LOG.dbg(f'running cmd: {command}')
            ret = cmd_update(opts)

        elif opts.cmd_detail:
            # detail files
            command = 'detail'
            LOG.dbg(f'running cmd: {command}')
            cmd_detail(opts)

        elif opts.cmd_remove:
            # remove dotfile
            command = 'remove'
            LOG.dbg(f'running cmd: {command}')
            cmd_remove(opts)

        elif opts.cmd_uninstall:
            # uninstall dotfile
            command = 'uninstall'
            LOG.dbg(f'running cmd: {command}')
            cmd_uninstall(opts)

    except UndefinedException as exc:
        LOG.err(exc)
        ret = False
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
        LOG.err(f'error (yaml): {exc}')
        return False
    except ConfigException as exc:
        LOG.err(f'error (config): {exc}')
        return False
    except UndefinedException as exc:
        LOG.err(f'error (deps): {exc}')
        return False
    except OptionsException as exc:
        LOG.err(f'error (options): {exc}')
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

    opts.debug_command()
    LOG.dbg(f'done executing command \"{command}\"')
    LOG.dbg(f'options loaded in {options_time}')
    LOG.dbg(f'command executed in {cmd_time}')

    if ret and opts.conf.save():
        LOG.log('config file updated')

    LOG.dbg(f'return {ret}')
    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
