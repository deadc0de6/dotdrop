"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
entry point
"""

import os
import sys
import subprocess
import utils
from docopt import docopt
from logger import Logger
from templategen import Templategen
from installer import Installer
from dotfile import Dotfile
from config import Cfg

VERSION = '0.2'
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
  dotdrop.py install [--profile=<profile>] [--cfg=<path>]
    [(-f | --force)] [--nodiff] [--dry]
  dotdrop.py compare [--profile=<profile>] [--cfg=<path>] [--files=<file key>]
  dotdrop.py list [--cfg=<path>]
  dotdrop.py import [--profile=<profile>] [--cfg=<path>]
    [(-l | --link)] [--dry] <paths>...
  dotdrop.py (-h | --help)
  dotdrop.py (-v | --version)

Options:
  --profile=<profiles>    Specify the profile to use [default: %s].
  --cfg=<path>            Path to the config [default: %s/config.yaml].
  --dry                   Dry run.
  --nodiff                Do not diff when installing [default: False].
  -l --link               Import and link [default: False].
  -f --force              Do not warn if exists [default: False].
  -v --version            Show version.
  -h --help               Show this screen.

""" % (BANNER, HOSTNAME, CUR)

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
                     diff=opts['installdiff'])
    installed = []
    for dotfile in dotfiles:
        if hasattr(dotfile, "link") and dotfile.link:
            r = inst.link(dotfile.src, dotfile.dst)
        else:
            r = inst.install(t, opts['profile'], dotfile.src, dotfile.dst)
        installed.extend(r)
    LOG.log('\n%u dotfile(s) installed.' % (len(installed)))
    return True


def compare(opts, conf, tmp, focus=""):
    dotfiles = conf.get_dotfiles(opts['profile'])
    if dotfiles == []:
        LOG.err('no dotfiles defined for this profile (\"%s\")' %
                (str(opts['profile'])))
        return False
    t = Templategen(base=opts['dotpath'])
    inst = Installer(create=opts['create'], backup=opts['backup'],
                     dry=opts['dry'], base=opts['dotpath'], quiet=True)

    # Selected files or directory must be comma separated without whitespace.
    # We will also make sure that the given arguments match the dotfile keys
    #   in the config file. If a key is not found, terminate the script and
    #   let the user know.
    if focus is not None:
        focus = focus.replace(" ", "")
        selected = focus.split(",")
        for selection in selected:
            exist = False
            for dotfile in dotfiles:
                if selection == dotfile.key:
                    exist = True
                    break
            if not exist:
                LOG.log('One of the keys is not found. Please double check '
                        'your arguments.')
                sys.exit(0)
    else:
        selected = []
        for dotfile in dotfiles:
            selected.append(dotfile.key)

    for dotfile in dotfiles:
        if dotfile.key in selected:
            LOG.log('diffing \"%s\" VS \"%s\"' % (dotfile.key, dotfile.dst))
            inst.compare(t, tmp, opts['profile'], dotfile.src, dotfile.dst)
    return len(dotfiles) > 0


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
        if os.path.exists(srcf):
            LOG.err('\"%s\" already exists, ignored !' % (srcf))
            continue
        conf.new(dotfile, opts['profile'], opts['link'])
        cmd = ['mkdir', '-p', '%s' % (os.path.dirname(srcf))]
        if opts['dry']:
            LOG.dry('would run: %s' % (' '.join(cmd)))
        else:
            utils.run(cmd, raw=False, log=False)
        if opts['link']:
            cmd = ['mv', '%s' % (dst), '%s' % (srcf)]
        else:
            cmd = ['cp', '-r', '%s' % (dst), '%s' % (srcf)]
        if opts['dry']:
            LOG.dry('would run: %s' % (' '.join(cmd)))
        else:
            utils.run(cmd, raw=False, log=False)
            if opts['link']:
                os.symlink(srcf, dst)
        LOG.sub('\"%s\" imported' % (path))
        cnt += 1
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


def header():
    LOG.log(BANNER)
    LOG.log("")


if __name__ == '__main__':
    ret = True
    args = docopt(USAGE, version=VERSION)
    conf = Cfg(args['--cfg'])
    focus = args['--files']

    opts = conf.get_configs()
    opts['dry'] = args['--dry']
    opts['profile'] = args['--profile']
    opts['safe'] = not args['--force']
    opts['installdiff'] = not args['--nodiff']
    opts['link'] = args['--link']

    header()

    try:

        if args['list']:
            list_profiles(conf)

        elif args['install']:
            ret = install(opts, conf)

        elif args['compare']:
            tmp = utils.get_tmpdir()
            if compare(opts, conf, tmp, focus):
                LOG.log('generated temporary files available under %s' % (tmp))
            else:
                os.rmdir(tmp)

        elif args['import']:
            importer(opts, conf, args['<paths>'])

    except KeyboardInterrupt:
        LOG.err('interrupted')

    if ret:
        sys.exit(0)
    sys.exit(1)
