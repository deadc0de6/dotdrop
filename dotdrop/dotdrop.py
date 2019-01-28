"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

entry point
"""

import os
import sys
import socket
from docopt import docopt

# local imports
from dotdrop.version import __version__ as VERSION
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
from dotdrop.installer import Installer
from dotdrop.updater import Updater
from dotdrop.comparator import Comparator
from dotdrop.dotfile import Dotfile
from dotdrop.config import Cfg
from dotdrop.utils import get_tmpdir, remove, strip_home, run
from dotdrop.linktypes import LinkTypes

LOG = Logger()
ENV_PROFILE = 'DOTDROP_PROFILE'
ENV_NOBANNER = 'DOTDROP_NOBANNER'
PROFILE = socket.gethostname()
if ENV_PROFILE in os.environ:
    PROFILE = os.environ[ENV_PROFILE]
TRANS_SUFFIX = 'trans'

BANNER = """     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v{}
                               |_|""".format(VERSION)

USAGE = """
{}

Usage:
  dotdrop install   [-tfndVbD] [-c <path>] [-p <profile>] [<key>...]
  dotdrop import    [-ldVb]    [-c <path>] [-p <profile>] <path>...
  dotdrop compare   [-Vb]      [-c <path>] [-p <profile>]
                               [-o <opts>] [-C <file>...] [-i <pattern>...]
  dotdrop update    [-fdVbk]   [-c <path>] [-p <profile>]
                               [-i <pattern>...] [<path>...]
  dotdrop listfiles [-VTb]     [-c <path>] [-p <profile>]
  dotdrop detail    [-Vb]      [-c <path>] [-p <profile>] [<key>...]
  dotdrop list      [-Vb]      [-c <path>]
  dotdrop --help
  dotdrop --version

Options:
  -p --profile=<profile>  Specify the profile to use [default: {}].
  -c --cfg=<path>         Path to the config [default: config.yaml].
  -C --file=<path>        Path of dotfile to compare.
  -i --ignore=<pattern>   Pattern to ignore.
  -o --dopts=<opts>       Diff options [default: ].
  -n --nodiff             Do not diff when installing.
  -t --temp               Install to a temporary directory for review.
  -T --template           Only template dotfiles.
  -D --showdiff           Show a diff before overwriting.
  -l --inv-link           Invert the value of "link_by_default" when importing.
  -f --force              Do not warn if exists.
  -k --key                Treat <path> as a dotfile key.
  -V --verbose            Be verbose.
  -d --dry                Dry run.
  -b --no-banner          Do not display the banner.
  -v --version            Show version.
  -h --help               Show this screen.

""".format(BANNER, PROFILE)

###########################################################
# entry point
###########################################################


def cmd_install(opts, conf, temporary=False, keys=[]):
    """install dotfiles for this profile"""
    dotfiles = conf.get_dotfiles(opts['profile'])
    if keys:
        # filtered dotfiles to install
        dotfiles = [d for d in dotfiles if d.key in set(keys)]
    if not dotfiles:
        msg = 'no dotfile to install for this profile (\"{}\")'
        LOG.warn(msg.format(opts['profile']))
        return False

    t = Templategen(profile=opts['profile'], base=opts['dotpath'],
                    variables=opts['variables'], debug=opts['debug'])
    tmpdir = None
    if temporary:
        tmpdir = get_tmpdir()
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], safe=opts['safe'],
                     base=opts['dotpath'], workdir=opts['workdir'],
                     diff=opts['installdiff'], debug=opts['debug'],
                     totemp=tmpdir, showdiff=opts['showdiff'])
    installed = []
    for dotfile in dotfiles:
        preactions = []
        if not temporary and dotfile.actions \
                and Cfg.key_actions_pre in dotfile.actions:
            for action in dotfile.actions[Cfg.key_actions_pre]:
                preactions.append(action)
        if opts['debug']:
            LOG.dbg('installing {}'.format(dotfile))
        if hasattr(dotfile, 'link') and dotfile.link == LinkTypes.PARENTS:
            r = inst.link(t, dotfile.src, dotfile.dst, actions=preactions)
        elif hasattr(dotfile, 'link') and dotfile.link == LinkTypes.CHILDREN:
            r = inst.linkall(t, dotfile.src, dotfile.dst, actions=preactions)
        else:
            src = dotfile.src
            tmp = None
            if dotfile.trans_r:
                tmp = apply_trans(opts, dotfile)
                if not tmp:
                    continue
                src = tmp
            r = inst.install(t, src, dotfile.dst, actions=preactions,
                             noempty=dotfile.noempty)
            if tmp:
                tmp = os.path.join(opts['dotpath'], tmp)
                if os.path.exists(tmp):
                    remove(tmp)
        if len(r) > 0:
            if not temporary and Cfg.key_actions_post in dotfile.actions:
                actions = dotfile.actions[Cfg.key_actions_post]
                # execute action
                for action in actions:
                    if opts['dry']:
                        LOG.dry('would execute action: {}'.format(action))
                    else:
                        if opts['debug']:
                            LOG.dbg('executing post action {}'.format(action))
                        action.execute()
        installed.extend(r)
    if temporary:
        LOG.log('\nInstalled to tmp \"{}\".'.format(tmpdir))
    LOG.log('\n{} dotfile(s) installed.'.format(len(installed)))
    return True


def cmd_compare(opts, conf, tmp, focus=[], ignore=[]):
    """compare dotfiles and return True if all identical"""
    dotfiles = conf.get_dotfiles(opts['profile'])
    if dotfiles == []:
        msg = 'no dotfile defined for this profile (\"{}\")'
        LOG.warn(msg.format(opts['profile']))
        return True
    # compare only specific files
    same = True
    selected = dotfiles
    if focus:
        selected = _select(focus, dotfiles)

    if len(selected) < 1:
        return False

    t = Templategen(profile=opts['profile'], base=opts['dotpath'],
                    variables=opts['variables'], debug=opts['debug'])
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], base=opts['dotpath'],
                     workdir=opts['workdir'], debug=opts['debug'])
    comp = Comparator(diffopts=opts['dopts'], debug=opts['debug'])

    for dotfile in selected:
        if opts['debug']:
            LOG.dbg('comparing {}'.format(dotfile))
        src = dotfile.src
        if not os.path.lexists(os.path.expanduser(dotfile.dst)):
            line = '=> compare {}: \"{}\" does not exist on local'
            LOG.log(line.format(dotfile.key, dotfile.dst))
            same = False
            continue

        tmpsrc = None
        if dotfile.trans_r:
            # apply transformation
            tmpsrc = apply_trans(opts, dotfile)
            if not tmpsrc:
                # could not apply trans
                same = False
                continue
            src = tmpsrc
        # install dotfile to temporary dir
        ret, insttmp = inst.install_to_temp(t, tmp, src, dotfile.dst)
        if not ret:
            # failed to install to tmp
            same = False
            continue
        ignores = list(set(ignore + dotfile.cmpignore))
        diff = comp.compare(insttmp, dotfile.dst, ignore=ignores)
        if tmpsrc:
            # clean tmp transformed dotfile if any
            tmpsrc = os.path.join(opts['dotpath'], tmpsrc)
            if os.path.exists(tmpsrc):
                remove(tmpsrc)
        if diff == '':
            if opts['debug']:
                line = '=> compare {}: diffing with \"{}\"'
                LOG.dbg(line.format(dotfile.key, dotfile.dst))
                LOG.dbg('same file')
        else:
            line = '=> compare {}: diffing with \"{}\"'
            LOG.log(line.format(dotfile.key, dotfile.dst))
            LOG.emph(diff)
            same = False

    return same


def cmd_update(opts, conf, paths, iskey=False, ignore=[]):
    """update the dotfile(s) from path(s) or key(s)"""
    ret = True
    updater = Updater(conf, opts['dotpath'], opts['dry'],
                      opts['safe'], iskey=iskey,
                      debug=opts['debug'], ignore=[])
    if not iskey:
        # update paths
        if opts['debug']:
            LOG.dbg('update by paths: {}'.format(paths))
        for path in paths:
            if not updater.update_path(path, opts['profile']):
                ret = False
    else:
        # update keys
        keys = paths
        if not keys:
            # if not provided, take all keys
            keys = [d.key for d in conf.get_dotfiles(opts['profile'])]
        if opts['debug']:
            LOG.dbg('update by keys: {}'.format(keys))
        for key in keys:
            if not updater.update_key(key, opts['profile']):
                ret = False
    return ret


def cmd_importer(opts, conf, paths):
    """import dotfile(s) from paths"""
    ret = True
    cnt = 0
    for path in paths:
        if opts['debug']:
            LOG.dbg('trying to import {}'.format(path))
        if not os.path.lexists(path):
            LOG.err('\"{}\" does not exist, ignored!'.format(path))
            ret = False
            continue
        dst = path.rstrip(os.sep)
        dst = os.path.abspath(dst)
        src = strip_home(dst)
        strip = '.' + os.sep
        if opts['keepdot']:
            strip = os.sep
        src = src.lstrip(strip)

        # create a new dotfile
        dotfile = Dotfile('', dst, src)

        linktype = LinkTypes(opts['link'])

        if opts['debug']:
            LOG.dbg('new dotfile: {}'.format(dotfile))

        # prepare hierarchy for dotfile
        srcf = os.path.join(opts['dotpath'], src)
        if not os.path.exists(srcf):
            cmd = ['mkdir', '-p', '{}'.format(os.path.dirname(srcf))]
            if opts['dry']:
                LOG.dry('would run: {}'.format(' '.join(cmd)))
            else:
                r, _ = run(cmd, raw=False, debug=opts['debug'], checkerr=True)
                if not r:
                    LOG.err('importing \"{}\" failed!'.format(path))
                    ret = False
                    continue
            cmd = ['cp', '-R', '-L', dst, srcf]
            if opts['dry']:
                LOG.dry('would run: {}'.format(' '.join(cmd)))
                if linktype == LinkTypes.PARENTS:
                    LOG.dry('would symlink {} to {}'.format(srcf, dst))
            else:
                r, _ = run(cmd, raw=False, debug=opts['debug'], checkerr=True)
                if not r:
                    LOG.err('importing \"{}\" failed!'.format(path))
                    ret = False
                    continue
                if linktype == LinkTypes.PARENTS:
                    remove(dst)
                    os.symlink(srcf, dst)
        retconf, dotfile = conf.new(dotfile, opts['profile'],
                                    link=linktype, debug=opts['debug'])
        if retconf:
            LOG.sub('\"{}\" imported'.format(path))
            cnt += 1
        else:
            LOG.warn('\"{}\" ignored'.format(path))
    if opts['dry']:
        LOG.dry('new config file would be:')
        LOG.raw(conf.dump())
    else:
        conf.save()
    LOG.log('\n{} file(s) imported.'.format(cnt))
    return ret


def cmd_list_profiles(conf):
    """list all profiles"""
    LOG.log('Available profile(s):')
    for p in conf.get_profiles():
        LOG.sub(p)
    LOG.log('')


def cmd_list_files(opts, conf, templateonly=False):
    """list all dotfiles for a specific profile"""
    if not opts['profile'] in conf.get_profiles():
        LOG.warn('unknown profile \"{}\"'.format(opts['profile']))
        return
    what = 'Dotfile(s)'
    if templateonly:
        what = 'Template(s)'
    LOG.emph('{} for profile \"{}\"\n'.format(what, opts['profile']))
    for dotfile in conf.get_dotfiles(opts['profile']):
        if templateonly:
            src = os.path.join(opts['dotpath'], dotfile.src)
            if not Templategen.is_template(src):
                continue
        LOG.log('{} (src: \"{}\", link: {})'.format(dotfile.key, dotfile.src,
                                                    dotfile.link))
        LOG.sub('{}'.format(dotfile.dst))
    LOG.log('')


def cmd_detail(opts, conf, keys=None):
    """list details on all files for all dotfile entries"""
    if not opts['profile'] in conf.get_profiles():
        LOG.warn('unknown profile \"{}\"'.format(opts['profile']))
        return
    dotfiles = conf.get_dotfiles(opts['profile'])
    if keys:
        # filtered dotfiles to install
        dotfiles = [d for d in dotfiles if d.key in set(keys)]
    LOG.emph('dotfiles details for profile \"{}\":\n'.format(opts['profile']))
    for d in dotfiles:
        _detail(opts['dotpath'], d)
    LOG.log('')


###########################################################
# helpers
###########################################################


def _detail(dotpath, dotfile):
    """print details on all files under a dotfile entry"""
    LOG.log('{} (dst: \"{}\", link: {})'.format(dotfile.key, dotfile.dst,
                                                dotfile.link))
    path = os.path.join(dotpath, os.path.expanduser(dotfile.src))
    if not os.path.isdir(path):
        template = 'no'
        if Templategen.is_template(path):
            template = 'yes'
        LOG.sub('{} (template:{})'.format(path, template))
    else:
        for root, dir, files in os.walk(path):
            for f in files:
                p = os.path.join(root, f)
                template = 'no'
                if Templategen.is_template(p):
                    template = 'yes'
                LOG.sub('{} (template:{})'.format(p, template))


def _header():
    """print the header"""
    LOG.log(BANNER)
    LOG.log('')


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


def apply_trans(opts, dotfile):
    """apply the read transformation to the dotfile
    return None if fails and new source if succeed"""
    src = dotfile.src
    new_src = '{}.{}'.format(src, TRANS_SUFFIX)
    trans = dotfile.trans_r
    if opts['debug']:
        LOG.dbg('executing transformation {}'.format(trans))
    s = os.path.join(opts['dotpath'], src)
    temp = os.path.join(opts['dotpath'], new_src)
    if not trans.transform(s, temp):
        msg = 'transformation \"{}\" failed for {}'
        LOG.err(msg.format(trans.key, dotfile.key))
        if new_src and os.path.exists(new_src):
            remove(new_src)
        return None
    return new_src


###########################################################
# main
###########################################################


def main():
    """entry point"""
    ret = True
    args = docopt(USAGE, version=VERSION)

    try:
        conf = Cfg(os.path.expanduser(args['--cfg']))
    except ValueError as e:
        LOG.err('Config format error: {}'.format(str(e)))
        return False

    opts = conf.get_settings()
    opts['dry'] = args['--dry']
    opts['profile'] = args['--profile']
    opts['safe'] = not args['--force']
    opts['installdiff'] = not args['--nodiff']
    opts['link'] = LinkTypes.NOLINK
    if opts['link_by_default']:
        opts['link'] = LinkTypes.PARENTS

    # Only invert link type from NOLINK to PARENTS and vice-versa
    if args['--inv-link'] and opts['link'] == LinkTypes.NOLINK:
        opts['link'] = LinkTypes.PARENTS
    if args['--inv-link'] and opts['link'] == LinkTypes.PARENTS:
        opts['link'] = LinkTypes.NOLINK

    opts['debug'] = args['--verbose']
    opts['variables'] = conf.get_variables(opts['profile'])
    opts['showdiff'] = opts['showdiff'] or args['--showdiff']

    if opts['debug']:
        LOG.dbg('config file: {}'.format(args['--cfg']))
        LOG.dbg('options:\n{}'.format(opts))
        LOG.dbg('configs:\n{}'.format(conf.dump()))

    # resolve dynamic paths
    conf.eval_dotfiles(opts['profile'], debug=opts['debug'])

    if ENV_NOBANNER not in os.environ \
            and opts['banner'] \
            and not args['--no-banner']:
        _header()

    try:

        if args['list']:
            # list existing profiles
            if opts['debug']:
                LOG.dbg('running cmd: list')
            cmd_list_profiles(conf)

        elif args['listfiles']:
            # list files for selected profile
            if opts['debug']:
                LOG.dbg('running cmd: listfiles')
            cmd_list_files(opts, conf, templateonly=args['--template'])

        elif args['install']:
            # install the dotfiles stored in dotdrop
            if opts['debug']:
                LOG.dbg('running cmd: install')
            ret = cmd_install(opts, conf, temporary=args['--temp'],
                              keys=args['<key>'])

        elif args['compare']:
            # compare local dotfiles with dotfiles stored in dotdrop
            if opts['debug']:
                LOG.dbg('running cmd: compare')
            tmp = get_tmpdir()
            opts['dopts'] = args['--dopts']
            ret = cmd_compare(opts, conf, tmp, focus=args['--file'],
                              ignore=args['--ignore'])
            # clean tmp directory
            remove(tmp)

        elif args['import']:
            # import dotfile(s)
            if opts['debug']:
                LOG.dbg('running cmd: import')
            ret = cmd_importer(opts, conf, args['<path>'])

        elif args['update']:
            # update a dotfile
            if opts['debug']:
                LOG.dbg('running cmd: update')
            iskey = args['--key']
            ret = cmd_update(opts, conf, args['<path>'], iskey=iskey,
                             ignore=args['--ignore'])

        elif args['detail']:
            # detail files
            if opts['debug']:
                LOG.dbg('running cmd: update')
            cmd_detail(opts, conf, keys=args['<key>'])

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False

    if opts['debug']:
        LOG.dbg('configs:\n{}'.format(conf.dump()))

    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
