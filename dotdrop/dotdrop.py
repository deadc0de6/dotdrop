"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

entry point
"""

import os
import sys
import time
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
    adapt_workers
from dotdrop.linktypes import LinkTypes
from dotdrop.exceptions import YamlException, UndefinedException

LOG = Logger()
TRANS_SUFFIX = 'trans'

###########################################################
# entry point
###########################################################


def action_executor(o, actions, defactions, templater, post=False):
    """closure for action execution"""
    def execute():
        """
        execute actions and return
        True, None if ok
        False, errstring if issue
        """
        s = 'pre' if not post else 'post'

        # execute default actions
        for action in defactions:
            if o.dry:
                LOG.dry('would execute def-{}-action: {}'.format(s,
                                                                 action))
                continue
            if o.debug:
                LOG.dbg('executing def-{}-action: {}'.format(s, action))
            ret = action.execute(templater=templater, debug=o.debug)
            if not ret:
                err = 'def-{}-action \"{}\" failed'.format(s, action.key)
                LOG.err(err)
                return False, err

        # execute actions
        for action in actions:
            if o.dry:
                LOG.dry('would execute {}-action: {}'.format(s, action))
                continue
            if o.debug:
                LOG.dbg('executing {}-action: {}'.format(s, action))
            ret = action.execute(templater=templater, debug=o.debug)
            if not ret:
                err = '{}-action \"{}\" failed'.format(s, action.key)
                LOG.err(err)
                return False, err
        return True, None
    return execute


def _dotfile_update(o, path, key=False):
    """
    update a dotfile pointed by path
    if key is false or by key (in path)
    """
    updater = Updater(o.dotpath, o.variables, o.conf,
                      dry=o.dry, safe=o.safe, debug=o.debug,
                      ignore=o.update_ignore,
                      showpatch=o.update_showpatch)
    if key:
        return updater.update_key(path)
    return updater.update_path(path)


def _dotfile_compare(o, dotfile, tmp):
    """
    compare a dotfile
    returns True if same
    """
    t = _get_templater(o)
    inst = Installer(create=o.create, backup=o.backup,
                     dry=o.dry, base=o.dotpath,
                     workdir=o.workdir, debug=o.debug,
                     backup_suffix=o.install_backup_suffix,
                     diff_cmd=o.diff_command)
    comp = Comparator(diff_cmd=o.diff_command, debug=o.debug)

    # add dotfile variables
    newvars = dotfile.get_dotfile_variables()
    t.add_tmp_vars(newvars=newvars)

    # dotfiles does not exist / not installed
    if o.debug:
        LOG.dbg('comparing {}'.format(dotfile))

    src = dotfile.src
    if not os.path.lexists(os.path.expanduser(dotfile.dst)):
        line = '=> compare {}: \"{}\" does not exist on destination'
        LOG.log(line.format(dotfile.key, dotfile.dst))
        return False

    # apply transformation
    tmpsrc = None
    if dotfile.trans_r:
        if o.debug:
            LOG.dbg('applying transformation before comparing')
        tmpsrc = apply_trans(o.dotpath, dotfile, t, debug=o.debug)
        if not tmpsrc:
            # could not apply trans
            return False
        src = tmpsrc

    # is a symlink pointing to itself
    asrc = os.path.join(o.dotpath, os.path.expanduser(src))
    adst = os.path.expanduser(dotfile.dst)
    if os.path.samefile(asrc, adst):
        if o.debug:
            line = '=> compare {}: diffing with \"{}\"'
            LOG.dbg(line.format(dotfile.key, dotfile.dst))
            LOG.dbg('points to itself')
        return True

    ignores = list(set(o.compare_ignore + dotfile.cmpignore))
    ignores = patch_ignores(ignores, dotfile.dst, debug=o.debug)

    insttmp = None
    if dotfile.template and Templategen.is_template(src, ignore=ignores):
        # install dotfile to temporary dir for compare
        ret, err, insttmp = inst.install_to_temp(t, tmp, src, dotfile.dst,
                                                 is_template=True,
                                                 chmod=dotfile.chmod)
        if not ret:
            # failed to install to tmp
            line = '=> compare {} error: {}'
            LOG.log(line.format(dotfile.key, err))
            LOG.err(err)
            return False
        src = insttmp

    # compare
    diff = comp.compare(src, dotfile.dst, ignore=ignores)

    # clean tmp transformed dotfile if any
    if tmpsrc:
        tmpsrc = os.path.join(o.dotpath, tmpsrc)
        if os.path.exists(tmpsrc):
            removepath(tmpsrc, LOG)

    # clean tmp template dotfile if any
    if insttmp:
        if os.path.exists(insttmp):
            removepath(insttmp, LOG)

    if diff != '':
        # print diff results
        line = '=> compare {}: diffing with \"{}\"'
        LOG.log(line.format(dotfile.key, dotfile.dst))
        if o.compare_fileonly:
            LOG.raw('<files are different>')
        else:
            LOG.emph(diff)
        return False
    # no difference
    if o.debug:
        line = '=> compare {}: diffing with \"{}\"'
        LOG.dbg(line.format(dotfile.key, dotfile.dst))
        LOG.dbg('same file')
    return True


def _dotfile_install(o, dotfile, tmpdir=None):
    """
    install a dotfile
    returns <success, dotfile key, err>
    """
    # installer
    inst = _get_install_installer(o, tmpdir=tmpdir)

    # templater
    t = _get_templater(o)

    # add dotfile variables
    newvars = dotfile.get_dotfile_variables()
    t.add_tmp_vars(newvars=newvars)

    preactions = []
    if not o.install_temporary:
        preactions.extend(dotfile.get_pre_actions())
    defactions = o.install_default_actions_pre
    pre_actions_exec = action_executor(o, preactions, defactions,
                                       t, post=False)

    if o.debug:
        LOG.dbg('installing dotfile: \"{}\"'.format(dotfile.key))
        LOG.dbg(dotfile.prt())

    ignores = list(set(o.install_ignore + dotfile.instignore))
    ignores = patch_ignores(ignores, dotfile.dst, debug=o.debug)

    is_template = dotfile.template and Templategen.is_template(
        dotfile.src,
        ignore=ignores,
    )
    if hasattr(dotfile, 'link') and dotfile.link == LinkTypes.LINK:
        # link
        r, err = inst.install(t, dotfile.src, dotfile.dst,
                              dotfile.link,
                              actionexec=pre_actions_exec,
                              is_template=is_template,
                              ignore=ignores,
                              chmod=dotfile.chmod)
    elif hasattr(dotfile, 'link') and \
            dotfile.link == LinkTypes.LINK_CHILDREN:
        # link_children
        r, err = inst.install(t, dotfile.src, dotfile.dst,
                              dotfile.link,
                              actionexec=pre_actions_exec,
                              is_template=is_template,
                              chmod=dotfile.chmod,
                              ignore=ignores)
    else:
        # nolink
        src = dotfile.src
        tmp = None
        if dotfile.trans_r:
            tmp = apply_trans(o.dotpath, dotfile, t, debug=o.debug)
            if not tmp:
                return False, dotfile.key, None
            src = tmp
        r, err = inst.install(t, src, dotfile.dst,
                              LinkTypes.NOLINK,
                              actionexec=pre_actions_exec,
                              noempty=dotfile.noempty,
                              ignore=ignores,
                              is_template=is_template,
                              chmod=dotfile.chmod)
        if tmp:
            tmp = os.path.join(o.dotpath, tmp)
            if os.path.exists(tmp):
                removepath(tmp, LOG)

    # check result of installation
    if r:
        # dotfile was installed
        if not o.install_temporary:
            defactions = o.install_default_actions_post
            postactions = dotfile.get_post_actions()
            post_actions_exec = action_executor(o, postactions, defactions,
                                                t, post=True)
            post_actions_exec()
    else:
        # dotfile was NOT installed
        if o.install_force_action:
            # pre-actions
            if o.debug:
                LOG.dbg('force pre action execution ...')
            pre_actions_exec()
            # post-actions
            if o.debug:
                LOG.dbg('force post action execution ...')
            defactions = o.install_default_actions_post
            postactions = dotfile.get_post_actions()
            post_actions_exec = action_executor(o, postactions, defactions,
                                                t, post=True)
            post_actions_exec()

    return r, dotfile.key, err


def cmd_install(o):
    """install dotfiles for this profile"""
    dotfiles = o.dotfiles
    prof = o.conf.get_profile()

    adapt_workers(o, LOG)

    pro_pre_actions = prof.get_pre_actions() if prof else []
    pro_post_actions = prof.get_post_actions() if prof else []

    if o.install_keys:
        # filtered dotfiles to install
        uniq = uniq_list(o.install_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
    if not dotfiles:
        msg = 'no dotfile to install for this profile (\"{}\")'
        LOG.warn(msg.format(o.profile))
        return False

    # the installer
    tmpdir = None
    if o.install_temporary:
        tmpdir = get_tmpdir()

    installed = []

    # execute profile pre-action
    if o.debug:
        LOG.dbg('run {} profile pre actions'.format(len(pro_pre_actions)))
    t = _get_templater(o)
    ret, err = action_executor(o, pro_pre_actions, [], t, post=False)()
    if not ret:
        return False

    # install each dotfile
    if o.workers > 1:
        # in parallel
        if o.debug:
            LOG.dbg('run with {} workers'.format(o.workers))
        ex = futures.ThreadPoolExecutor(max_workers=o.workers)

        wait_for = []
        for dotfile in dotfiles:
            j = ex.submit(_dotfile_install, o, dotfile, tmpdir=tmpdir)
            wait_for.append(j)
        # check result
        for f in futures.as_completed(wait_for):
            r, key, err = f.result()
            if r:
                installed.append(key)
            elif err:
                LOG.err('installing \"{}\" failed: {}'.format(key,
                                                              err))
    else:
        # sequentially
        for dotfile in dotfiles:
            r, key, err = _dotfile_install(o, dotfile, tmpdir=tmpdir)
            # check result
            if r:
                installed.append(key)
            elif err:
                LOG.err('installing \"{}\" failed: {}'.format(key,
                                                              err))

    # execute profile post-action
    if len(installed) > 0 or o.install_force_action:
        if o.debug:
            msg = 'run {} profile post actions'
            LOG.dbg(msg.format(len(pro_post_actions)))
        ret, err = action_executor(o, pro_post_actions, [], t, post=False)()
        if not ret:
            return False

    if o.debug:
        LOG.dbg('install done: installed \"{}\"'.format(','.join(installed)))

    if o.install_temporary:
        LOG.log('\ninstalled to tmp \"{}\".'.format(tmpdir))
    LOG.log('\n{} dotfile(s) installed.'.format(len(installed)))
    return True


def cmd_compare(o, tmp):
    """compare dotfiles and return True if all identical"""
    dotfiles = o.dotfiles
    if not dotfiles:
        msg = 'no dotfile defined for this profile (\"{}\")'
        LOG.warn(msg.format(o.profile))
        return True

    # compare only specific files
    selected = dotfiles
    if o.compare_focus:
        selected = _select(o.compare_focus, dotfiles)

    if len(selected) < 1:
        LOG.log('\nno dotfile to compare')
        return False

    same = True
    cnt = 0
    if o.workers > 1:
        # in parallel
        if o.debug:
            LOG.dbg('run with {} workers'.format(o.workers))
        ex = futures.ThreadPoolExecutor(max_workers=o.workers)
        wait_for = []
        for dotfile in selected:
            j = ex.submit(_dotfile_compare, o, dotfile, tmp)
            wait_for.append(j)
        # check result
        for f in futures.as_completed(wait_for):
            if not dotfile.src and not dotfile.dst:
                # ignore fake dotfile
                continue
            if not f.result():
                same = False
            cnt += 1
    else:
        # sequentially
        for dotfile in selected:
            if not dotfile.src and not dotfile.dst:
                # ignore fake dotfile
                continue
            if not _dotfile_compare(o, dotfile, tmp):
                same = False
            cnt += 1

    LOG.log('\n{} dotfile(s) compared.'.format(cnt))
    return same


def cmd_update(o):
    """update the dotfile(s) from path(s) or key(s)"""
    cnt = 0
    paths = o.update_path
    iskey = o.update_iskey

    if o.profile not in [p.key for p in o.profiles]:
        LOG.err('no such profile \"{}\"'.format(o.profile))
        return False

    adapt_workers(o, LOG)

    if not paths:
        # update the entire profile
        if iskey:
            if o.debug:
                LOG.dbg('update by keys: {}'.format(paths))
            paths = [d.key for d in o.dotfiles]
        else:
            if o.debug:
                LOG.dbg('update by paths: {}'.format(paths))
            paths = [d.dst for d in o.dotfiles]
        msg = 'Update all dotfiles for profile \"{}\"'.format(o.profile)
        if o.safe and not LOG.ask(msg):
            LOG.log('\n{} file(s) updated.'.format(cnt))
            return False

    if not paths:
        LOG.log('\nno dotfile to update')
        return True

    if o.debug:
        LOG.dbg('dotfile to update: {}'.format(paths))

    # update each dotfile
    if o.workers > 1:
        # in parallel
        if o.debug:
            LOG.dbg('run with {} workers'.format(o.workers))
        ex = futures.ThreadPoolExecutor(max_workers=o.workers)
        wait_for = []
        for path in paths:
            j = ex.submit(_dotfile_update, o, path, key=iskey)
            wait_for.append(j)
        # check result
        for f in futures.as_completed(wait_for):
            if f.result():
                cnt += 1
    else:
        # sequentially
        for path in paths:
            if _dotfile_update(o, path, key=iskey):
                cnt += 1

    LOG.log('\n{} file(s) updated.'.format(cnt))
    return cnt == len(paths)


def cmd_importer(o):
    """import dotfile(s) from paths"""
    ret = True
    cnt = 0
    paths = o.import_path
    importer = Importer(o.profile, o.conf, o.dotpath, o.diff_command,
                        dry=o.dry, safe=o.safe, debug=o.debug,
                        keepdot=o.keepdot, ignore=o.import_ignore)

    for path in paths:
        r = importer.import_path(path, import_as=o.import_as,
                                 import_link=o.import_link,
                                 import_mode=o.import_mode)
        if r < 0:
            ret = False
        elif r > 0:
            cnt += 1

    if o.dry:
        LOG.dry('new config file would be:')
        LOG.raw(o.conf.dump())
    else:
        o.conf.save()
    LOG.log('\n{} file(s) imported.'.format(cnt))

    return ret


def cmd_list_profiles(o):
    """list all profiles"""
    LOG.emph('Available profile(s):\n')
    for p in o.profiles:
        if o.profiles_grepable:
            fmt = '{}'.format(p.key)
            LOG.raw(fmt)
        else:
            LOG.sub(p.key, end='')
            LOG.log(' ({} dotfiles)'.format(len(p.dotfiles)))
    LOG.log('')


def cmd_files(o):
    """list all dotfiles for a specific profile"""
    if o.profile not in [p.key for p in o.profiles]:
        LOG.warn('unknown profile \"{}\"'.format(o.profile))
        return
    what = 'Dotfile(s)'
    if o.files_templateonly:
        what = 'Template(s)'
    LOG.emph('{} for profile \"{}\":\n'.format(what, o.profile))
    for dotfile in o.dotfiles:
        if o.files_templateonly:
            src = os.path.join(o.dotpath, dotfile.src)
            if not Templategen.is_template(src):
                continue
        if o.files_grepable:
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


def cmd_detail(o):
    """list details on all files for all dotfile entries"""
    if o.profile not in [p.key for p in o.profiles]:
        LOG.warn('unknown profile \"{}\"'.format(o.profile))
        return
    dotfiles = o.dotfiles
    if o.detail_keys:
        # filtered dotfiles to install
        uniq = uniq_list(o.details_keys)
        dotfiles = [d for d in dotfiles if d.key in uniq]
    LOG.emph('dotfiles details for profile \"{}\":\n'.format(o.profile))
    for d in dotfiles:
        _detail(o.dotpath, d)
    LOG.log('')


def cmd_remove(o):
    """remove dotfile from dotpath and from config"""
    paths = o.remove_path
    iskey = o.remove_iskey

    if not paths:
        LOG.log('no dotfile to remove')
        return False
    if o.debug:
        LOG.dbg('dotfile(s) to remove: {}'.format(','.join(paths)))

    removed = []
    for key in paths:
        if not iskey:
            # by path
            dotfiles = o.conf.get_dotfile_by_dst(key)
            if not dotfiles:
                LOG.warn('{} ignored, does not exist'.format(key))
                continue
        else:
            # by key
            dotfile = o.conf.get_dotfile(key)
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

            if o.debug:
                LOG.dbg('removing {}'.format(key))

            # make sure is part of the profile
            if dotfile.key not in [d.key for d in o.dotfiles]:
                msg = '{} ignored, not associated to this profile'
                LOG.warn(msg.format(key))
                continue
            profiles = o.conf.get_profiles_by_dotfile_key(k)
            pkeys = ','.join([p.key for p in profiles])
            if o.dry:
                LOG.dry('would remove {} from {}'.format(dotfile, pkeys))
                continue
            msg = 'Remove \"{}\" from all these profiles: {}'.format(k, pkeys)
            if o.safe and not LOG.ask(msg):
                return False
            if o.debug:
                LOG.dbg('remove dotfile: {}'.format(dotfile))

            for profile in profiles:
                if not o.conf.del_dotfile_from_profile(dotfile, profile):
                    return False
            if not o.conf.del_dotfile(dotfile):
                return False

            # remove dotfile from dotpath
            dtpath = os.path.join(o.dotpath, dotfile.src)
            removepath(dtpath, LOG)
            # remove empty directory
            parent = os.path.dirname(dtpath)
            # remove any empty parent up to dotpath
            while parent != o.dotpath:
                if os.path.isdir(parent) and not os.listdir(parent):
                    msg = 'Remove empty dir \"{}\"'.format(parent)
                    if o.safe and not LOG.ask(msg):
                        break
                    removepath(parent, LOG)
                parent = os.path.dirname(parent)
            removed.append(dotfile.key)

    if o.dry:
        LOG.dry('new config file would be:')
        LOG.raw(o.conf.dump())
    else:
        o.conf.save()
    if removed:
        LOG.log('\ndotfile(s) removed: {}'.format(','.join(removed)))
    else:
        LOG.log('\nno dotfile removed')
    return True


###########################################################
# helpers
###########################################################


def _get_install_installer(o, tmpdir=None):
    """get an installer instance for cmd_install"""
    inst = Installer(create=o.create, backup=o.backup,
                     dry=o.dry, safe=o.safe,
                     base=o.dotpath, workdir=o.workdir,
                     diff=o.install_diff, debug=o.debug,
                     totemp=tmpdir,
                     showdiff=o.install_showdiff,
                     backup_suffix=o.install_backup_suffix,
                     diff_cmd=o.diff_command)
    return inst


def _get_templater(o):
    """get an templater instance"""
    t = Templategen(base=o.dotpath, variables=o.variables,
                    func_file=o.func_file, filter_file=o.filter_file,
                    debug=o.debug)
    return t


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
            for f in files:
                p = os.path.join(root, f)
                template = 'no'
                if dotfile.template and Templategen.is_template(p):
                    template = 'yes'
                LOG.sub('{} (template:{})'.format(p, template))


def _select(selections, dotfiles):
    selected = []
    for selection in selections:
        df = next(
            (x for x in dotfiles
                if os.path.expanduser(x.dst) == os.path.expanduser(selection)),
            None
        )
        if df:
            selected.append(df)
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
    if debug:
        LOG.dbg('executing transformation: {}'.format(trans))
    s = os.path.join(dotpath, src)
    temp = os.path.join(dotpath, new_src)
    if not trans.transform(s, temp, templater=templater, debug=debug):
        msg = 'transformation \"{}\" failed for {}'
        LOG.err(msg.format(trans.key, dotfile.key))
        if new_src and os.path.exists(new_src):
            removepath(new_src, LOG)
        return None
    return new_src


###########################################################
# main
###########################################################


def main():
    """entry point"""
    # check dependencies are met
    try:
        dependencies_met()
    except Exception as e:
        LOG.err(e)
        return False

    t0 = time.time()
    try:
        o = Options()
    except YamlException as e:
        LOG.err('config error: {}'.format(str(e)))
        return False
    except UndefinedException as e:
        LOG.err('config error: {}'.format(str(e)))
        return False

    if o.debug:
        LOG.dbg('\n\n')
    options_time = time.time() - t0

    ret = True
    t0 = time.time()
    command = ''
    try:

        if o.cmd_profiles:
            # list existing profiles
            command = 'profiles'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            cmd_list_profiles(o)

        elif o.cmd_files:
            # list files for selected profile
            command = 'files'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            cmd_files(o)

        elif o.cmd_install:
            # install the dotfiles stored in dotdrop
            command = 'install'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            ret = cmd_install(o)

        elif o.cmd_compare:
            # compare local dotfiles with dotfiles stored in dotdrop
            command = 'compare'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            tmp = get_tmpdir()
            ret = cmd_compare(o, tmp)
            # clean tmp directory
            removepath(tmp, LOG)

        elif o.cmd_import:
            # import dotfile(s)
            command = 'import'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            ret = cmd_importer(o)

        elif o.cmd_update:
            # update a dotfile
            command = 'update'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            ret = cmd_update(o)

        elif o.cmd_detail:
            # detail files
            command = 'detail'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            cmd_detail(o)

        elif o.cmd_remove:
            # remove dotfile
            command = 'remove'
            if o.debug:
                LOG.dbg('running cmd: {}'.format(command))
            cmd_remove(o)

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False
    cmd_time = time.time() - t0

    if o.debug:
        LOG.dbg('done executing command \"{}\"'.format(command))
        LOG.dbg('options loaded in {}'.format(options_time))
        LOG.dbg('command executed in {}'.format(cmd_time))

    if ret and o.conf.save():
        LOG.log('config file updated')

    if o.debug:
        LOG.dbg('return {}'.format(ret))
    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
