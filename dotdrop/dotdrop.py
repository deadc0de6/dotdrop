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
except:
    errmsg = '''
Dotdrop has been updated to be included in pypi and
the way it needs to be called has slightly changed.

If you want to keep it as a submodule, simply do the following:

First get the latest version of dotdrop:
    $ git submodule update --init --recursive
And then re-run the bootstrap script to update \"dotdrop.sh\":
    $ ./dotdrop/bootstrap.sh

Otherwise you can simply install dotdrop from pypi:
    $ sudo pip3 install dotdrop

see https://github.com/deadc0de6/dotdrop#migrate-from-submodule
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

BANNER = """     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v%s
                               |_|""" % (VERSION)

USAGE = """
%s

Usage:
  dotdrop install   [-fndVc <path>] [--profile=<profile>]
  dotdrop compare   [-Vc <path>] [--profile=<profile>] [--files=<files>]
  dotdrop import    [-ldVc <path>] [--profile=<profile>] <paths>...
  dotdrop listfiles [-Vc <path>] [--profile=<profile>]
  dotdrop list      [-Vc <path>]
  dotdrop --help
  dotdrop --version

Options:
  --profile=<profile>     Specify the profile to use [default: %s].
  -c --cfg=<path>         Path to the config [default: config.yaml].
  --files=<files>         Comma separated list of files to compare.
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
                (str(opts['profile'])))
        return False
    t = Templategen(base=opts['dotpath'])
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], safe=opts['safe'], base=opts['dotpath'],
                     diff=opts['installdiff'], quiet=opts['quiet'])
    installed = []
    for dotfile in dotfiles:
        if hasattr(dotfile, 'link') and dotfile.link:
            r = inst.link(dotfile.src, dotfile.dst)
        else:
            r = inst.install(t, opts['profile'], dotfile.src, dotfile.dst)
        if len(r) > 0 and len(dotfile.actions) > 0:
            # execute action
            for action in dotfile.actions:
                action.execute()
        installed.extend(r)
    LOG.log('\n%u dotfile(s) installed.' % (len(installed)))
    return True


def compare(opts, conf, tmp, focus=None):
    dotfiles = conf.get_dotfiles(opts['profile'])
    if dotfiles == []:
        LOG.err('no dotfiles defined for this profile (\"%s\")' %
                (str(opts['profile'])))
        return False
    t = Templategen(base=opts['dotpath'])
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], base=opts['dotpath'],
                     quiet=opts['quiet'])

    # compare only specific files
    selected = dotfiles
    if focus:
        selected = []
        for selection in focus.replace(' ', '').split(','):
            df = next((x for x in dotfiles if x.dst == selection), None)
            if df:
                selected.append(df)
            else:
                LOG.err('no dotfile matches \"%s\"' % (selection))

    for dotfile in selected:
        same, diff = inst.compare(t, tmp, opts['profile'],
                                  dotfile.src, dotfile.dst)
        if same:
            if not opts['quiet']:
                LOG.log('diffing \"%s\" VS \"%s\"' % (dotfile.key,
                                                      dotfile.dst))
                LOG.raw('same file')
        else:
            LOG.log('diffing \"%s\" VS \"%s\"' % (dotfile.key, dotfile.dst))
            LOG.emph(diff)

    return len(selected) > 0


def importer(opts, conf, paths):
    home = os.path.expanduser('~')
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
                run(cmd, raw=False, log=False)
            cmd = ['cp', '-R', '-L', dst, srcf]
            if opts['dry']:
                LOG.dry('would run: %s' % (' '.join(cmd)))
                if opts['link']:
                    LOG.dry('would symlink %s to %s' % (srcf, dst))
            else:
                run(cmd, raw=False, log=False)
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
    LOG.log("")


def main():
    ret = True
    args = docopt(USAGE, version=VERSION)
    try:
        conf = Cfg(args['--cfg'])
    except ValueError as e:
        LOG.err('error: %s' % (str(e)))
        return False

    opts = conf.get_configs()
    opts['dry'] = args['--dry']
    opts['profile'] = args['--profile']
    opts['safe'] = not args['--force']
    opts['installdiff'] = not args['--nodiff']
    opts['link'] = args['--link']
    opts['quiet'] = not args['--verbose']

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
            if compare(opts, conf, tmp, args['--files']):
                LOG.raw('\ntemporary files available under %s' % (tmp))
            else:
                os.rmdir(tmp)

        elif args['import']:
            # import dotfile(s)
            importer(opts, conf, args['<paths>'])

    except KeyboardInterrupt:
        LOG.err('interrupted')
        ret = False

    return ret


if __name__ == '__main__':
    if main():
        sys.exit(0)
    sys.exit(1)
