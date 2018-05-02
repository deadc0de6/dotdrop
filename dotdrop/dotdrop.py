"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
entry point
"""

import os
import sys
import subprocess
from docopt import docopt

# local imports
try:
    from . import __version__ as VERSION
except ImportError:
    errmsg = '''
Dotdrop has been updated to be included in pypi and
the way it needs to be called has slightly changed.

See https://github.com/deadc0de6/dotdrop/wiki/migrate-from-submodule
'''
    print(errmsg)
    sys.exit(1)
from .logger import Logger
from .templategen import Templategen
from .installer import Installer
from .dotfile import Dotfile
from .config import Cfg
from .utils import *

CUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = Logger()
HOSTNAME = os.uname()[1]
TILD = '~'
TRANS_SUFFIX = 'trans'

BANNER = """     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v%s
                               |_|""" % (VERSION)

USAGE = """
%s

Usage:
  dotdrop install   [-fndV] [-c <path>] [-p <profile>]
  dotdrop import    [-ldV]  [-c <path>] [-p <profile>] <paths>...
  dotdrop compare   [-V]    [-c <path>] [-p <profile>]
                            [-o <opts>] [--files=<files>]
  dotdrop update    [-fdV]  [-c <path>] <path>
  dotdrop listfiles [-V]    [-c <path>] [-p <profile>]
  dotdrop list      [-V]    [-c <path>]
  dotdrop --help
  dotdrop --version

Options:
  -p --profile=<profile>  Specify the profile to use [default: %s].
  -c --cfg=<path>         Path to the config [default: config.yaml].
  --files=<files>         Comma separated list of files to compare.
  -o --dopts=<opts>       Diff options [default: ].
  -n --nodiff             Do not diff when installing.
  -l --link               Import and link.
  -f --force              Do not warn if exists.
  -V --verbose            Be verbose.
  -d --dry                Dry run.
  -v --version            Show version.
  -h --help               Show this screen.

""" % (BANNER, HOSTNAME)

###########################################################
# entry point
###########################################################


def install(opts, conf):
    dotfiles = conf.get_dotfiles(opts['profile'])
    if dotfiles == []:
        LOG.err('no dotfiles defined for this profile (\"%s\")' %
                (opts['profile']))
        return False
    t = Templategen(base=opts['dotpath'])
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], safe=opts['safe'], base=opts['dotpath'],
                     diff=opts['installdiff'], debug=opts['debug'])
    installed = []
    for dotfile in dotfiles:
        if hasattr(dotfile, 'link') and dotfile.link:
            r = inst.link(dotfile.src, dotfile.dst)
        else:
            src = dotfile.src
            tmp = None
            if dotfile.trans:
                tmp = '%s.%s' % (src, TRANS_SUFFIX)
                err = False
                for trans in dotfile.trans:
                    s = os.path.join(opts['dotpath'], src)
                    temp = os.path.join(opts['dotpath'], tmp)
                    if not trans.transform(s, temp):
                        msg = 'transformation \"%s\" failed for %s'
                        LOG.err(msg % (trans.key, dotfile.key))
                        err = True
                        break
                if err:
                    if tmp and os.path.exists(tmp):
                        remove(tmp)
                    continue
                src = tmp
            r = inst.install(t, opts['profile'], src, dotfile.dst)
            if tmp:
                tmp = os.path.join(opts['dotpath'], tmp)
                if os.path.exists(tmp):
                    remove(tmp)
        if len(r) > 0 and len(dotfile.actions) > 0:
            # execute action
            for action in dotfile.actions:
                action.execute()
        installed.extend(r)
    LOG.log('\n%u dotfile(s) installed.' % (len(installed)))
    return True


def compare(opts, conf, tmp, focus=None):
    '''compare dotfiles and return True if all same'''
    dotfiles = conf.get_dotfiles(opts['profile'])
    if dotfiles == []:
        LOG.err('no dotfiles defined for this profile (\"%s\")' %
                (opts['profile']))
        return True
    t = Templategen(base=opts['dotpath'])
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], base=opts['dotpath'],
                     debug=opts['debug'])

    # compare only specific files
    ret = True
    selected = dotfiles
    if focus:
        selected = []
        for selection in focus.replace(' ', '').split(','):
            df = next((x for x in dotfiles if x.dst == selection), None)
            if df:
                selected.append(df)
            else:
                LOG.err('no dotfile matches \"%s\"' % (selection))
                ret = False

    if len(selected) < 1:
        return ret

    for dotfile in selected:
        if dotfile.trans:
            msg = 'ignore %s as it uses transformation(s)'
            LOG.log(msg % (dotfile.key))
            continue
        same, diff = inst.compare(t, tmp, opts['profile'],
                                  dotfile.src, dotfile.dst,
                                  opts=opts['dopts'])
        if same:
            if not opts['debug']:
                LOG.dbg('diffing \"%s\" VS \"%s\"' % (dotfile.key,
                                                      dotfile.dst))
                LOG.raw('same file')
        else:
            LOG.log('diffing \"%s\" VS \"%s\"' % (dotfile.key, dotfile.dst))
            LOG.emph(diff)
            ret = False

    return ret


def update(opts, conf, path):
    if not os.path.exists(path):
        LOG.err('\"%s\" does not exist!' % (path))
        return False
    home = os.path.expanduser(TILD)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    # normalize the path
    if path.startswith(home):
        path = path.lstrip(home)
        path = os.path.join(TILD, path)
    dotfiles = conf.get_dotfiles(opts['profile'])
    subs = [d for d in dotfiles if d.dst == path]
    if not subs:
        LOG.err('\"%s\" is not managed!' % (path))
        return False
    if len(subs) > 1:
        found = ','.join([d.src for d in dotfiles])
        LOG.err('multiple dotfiles found: %s' % (found))
        return False
    dotfile = subs[0]
    src = os.path.join(conf.get_abs_dotpath(opts['dotpath']), dotfile.src)
    if Templategen.get_marker() in open(src, 'r').read():
        LOG.warn('\"%s\" uses template, please update manually' % (src))
        return False
    cmd = ['cp', '-R', '-L', os.path.expanduser(path), src]
    if opts['dry']:
        LOG.dry('would run: %s' % (' '.join(cmd)))
    else:
        msg = 'Overwrite \"%s\" with \"%s\"?' % (src, path)
        if opts['safe'] and not LOG.ask(msg):
            return False
        else:
            run(cmd, raw=False)
            LOG.log('\"%s\" updated from \"%s\".' % (src, path))
    return True


def importer(opts, conf, paths):
    home = os.path.expanduser(TILD)
    cnt = 0
    for path in paths:
        if not os.path.exists(path):
            LOG.err('\"%s\" does not exist, ignored !' % (path))
            continue
        dst = path.rstrip(os.sep)
        key = dst.split(os.sep)[-1]
        if key == 'config':
            key = '_'.join(dst.split(os.sep)[-2:])
        key = key.lstrip('.').lower()
        if os.path.isdir(dst):
            key = 'd_%s' % (key)
        else:
            key = 'f_%s' % (key)
        src = dst
        if dst.startswith(home):
            src = dst[len(home):]
        src = src.lstrip('.' + os.sep)
        dotfile = Dotfile(key, dst, src)
        srcf = os.path.join(CUR, opts['dotpath'], src)
        retconf = conf.new(dotfile, opts['profile'], opts['link'])
        if not os.path.exists(srcf):
            cmd = ['mkdir', '-p', '%s' % (os.path.dirname(srcf))]
            if opts['dry']:
                LOG.dry('would run: %s' % (' '.join(cmd)))
            else:
                run(cmd, raw=False)
            cmd = ['cp', '-R', '-L', dst, srcf]
            if opts['dry']:
                LOG.dry('would run: %s' % (' '.join(cmd)))
                if opts['link']:
                    LOG.dry('would symlink %s to %s' % (srcf, dst))
            else:
                run(cmd, raw=False)
                if opts['link']:
                    remove(dst)
                    os.symlink(srcf, dst)
        if retconf:
            LOG.sub('\"%s\" imported' % (path))
            cnt += 1
        else:
            LOG.warn('\"%s\" ignored' % (path))
    if opts['dry']:
        LOG.dry('new config file would be:')
        LOG.raw(conf.dump())
    else:
        conf.save()
    LOG.log('\n%u file(s) imported.' % (cnt))


def list_profiles(conf):
    LOG.log('Available profile(s):')
    for p in conf.get_profiles():
        LOG.sub(p)
    LOG.log('')


def list_files(opts, conf):
    if not opts['profile'] in conf.get_profiles():
        LOG.warn('unknown profile \"%s\"' % (opts['profile']))
        return
    LOG.log('Dotfile(s) for profile \"%s\":\n' % (opts['profile']))
    for dotfile in conf.get_dotfiles(opts['profile']):
        LOG.log('%s (file: \"%s\", link: %s)' % (dotfile.key, dotfile.src,
                                                 str(dotfile.link)))
        LOG.sub('%s' % (dotfile.dst))
    LOG.log('')


def header():
    LOG.log(BANNER)
    LOG.log('')


def main():
    ret = True
    args = docopt(USAGE, version=VERSION)
    try:
        conf = Cfg(os.path.expanduser(args['--cfg']))
    except ValueError as e:
        LOG.err('error: %s' % (str(e)))
        return False

    opts = conf.get_configs()
    opts['dry'] = args['--dry']
    opts['profile'] = args['--profile']
    opts['safe'] = not args['--force']
    opts['installdiff'] = not args['--nodiff']
    opts['link'] = args['--link']
    opts['debug'] = not args['--verbose']

    if opts['debug']:
        LOG.debug = True

    header()

    try:

        if args['list']:
            # list existing profiles
            list_profiles(conf)

        elif args['listfiles']:
            # list files for selected profile
            list_files(opts, conf)

        elif args['install']:
            # install the dotfiles stored in dotdrop
            ret = install(opts, conf)

        elif args['compare']:
            # compare local dotfiles with dotfiles stored in dotdrop
            tmp = get_tmpdir()
            opts['dopts'] = args['--dopts']
            ret = compare(opts, conf, tmp, args['--files'])
            if os.listdir(tmp):
                LOG.raw('\ntemporary files available under %s' % (tmp))
            else:
                os.rmdir(tmp)

        elif args['import']:
            # import dotfile(s)
            importer(opts, conf, args['<paths>'])

        elif args['update']:
            # update a dotfile
            update(opts, conf, args['<path>'])

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False

    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
