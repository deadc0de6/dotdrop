"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

stores all options to use across dotdrop
"""

import os
import sys
import socket
from docopt import docopt

# local imports
from dotdrop.version import __version__ as VERSION
from dotdrop.linktypes import LinkTypes
from dotdrop.logger import Logger
from dotdrop.cfg_yaml import Cfg

ENV_PROFILE = 'DOTDROP_PROFILE'
ENV_CONFIG = 'DOTDROP_CONFIG'
ENV_NOBANNER = 'DOTDROP_NOBANNER'
ENV_DEBUG = 'DOTDROP_DEBUG'
ENV_NODEBUG = 'DOTDROP_FORCE_NODEBUG'
ENV_XDG = 'XDG_CONFIG_HOME'
BACKUP_SUFFIX = '.dotdropbak'

PROFILE = socket.gethostname()
if ENV_PROFILE in os.environ:
    PROFILE = os.environ[ENV_PROFILE]

NAME = 'dotdrop'
CONFIG = 'config.yaml'
HOMECFG = '~/.config/{}'.format(NAME)
ETCXDGCFG = '/etc/xdg/{}'.format(NAME)
ETCCFG = '/etc/{}'.format(NAME)

OPT_LINK = {
    LinkTypes.NOLINK.name.lower(): LinkTypes.NOLINK,
    LinkTypes.LINK.name.lower(): LinkTypes.LINK,
    LinkTypes.LINK_CHILDREN.name.lower(): LinkTypes.LINK_CHILDREN}

BANNER = """     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v{}
                               |_|""".format(VERSION)

USAGE = """
{}

Usage:
  dotdrop install   [-VbtfndD] [-c <path>] [-p <profile>] [<key>...]
  dotdrop import    [-Vbd]     [-c <path>] [-p <profile>] [-l <link>] <path>...
  dotdrop compare   [-Vb]      [-c <path>] [-p <profile>]
                               [-o <opts>] [-C <file>...] [-i <pattern>...]
  dotdrop update    [-VbfdkP]  [-c <path>] [-p <profile>]
                               [-i <pattern>...] [<path>...]
  dotdrop listfiles [-VbT]     [-c <path>] [-p <profile>]
  dotdrop detail    [-Vb]      [-c <path>] [-p <profile>] [<key>...]
  dotdrop list      [-Vb]      [-c <path>]
  dotdrop --help
  dotdrop --version

Options:
  -p --profile=<profile>  Specify the profile to use [default: {}].
  -c --cfg=<path>         Path to the config.
  -C --file=<path>        Path of dotfile to compare.
  -i --ignore=<pattern>   Pattern to ignore.
  -o --dopts=<opts>       Diff options [default: ].
  -l --link=<link>        "link_on_import" (nolink|link|link_children).
  -n --nodiff             Do not diff when installing.
  -t --temp               Install to a temporary directory for review.
  -T --template           Only template dotfiles.
  -D --showdiff           Show a diff before overwriting.
  -P --show-patch         Provide a one-liner to manually patch template.
  -f --force              Do not ask user confirmation for anything.
  -k --key                Treat <path> as a dotfile key.
  -V --verbose            Be verbose.
  -d --dry                Dry run.
  -b --no-banner          Do not display the banner.
  -v --version            Show version.
  -h --help               Show this screen.
""".format(BANNER, PROFILE)


class AttrMonitor:
    _set_attr_err = False

    def __setattr__(self, key, value):
        """monitor attribute setting"""
        if not hasattr(self, key) and self._set_attr_err:
            self._attr_change(key)
        super(AttrMonitor, self).__setattr__(key, value)

    def _attr_set(self, attr):
        """do something when unexistent attr is set"""
        pass


class Options(AttrMonitor):

    def __init__(self, args=None):
        """constructor
        @args: argument dictionary (if None use sys)
        """
        self.args = args
        if not args:
            self.args = docopt(USAGE, version=VERSION)
        self.log = Logger()
        self.debug = self.args['--verbose']
        if not self.debug and ENV_DEBUG in os.environ:
            self.debug = True
        if ENV_NODEBUG in os.environ:
            self.debug = False
        self.profile = self.args['--profile']
        self.confpath = self._get_config_path()
        if self.debug:
            self.log.dbg('config file: {}'.format(self.confpath))

        self._read_config(self.profile)
        self._apply_args()
        self._fill_attr()
        if ENV_NOBANNER not in os.environ \
           and self.banner \
           and not self.args['--no-banner']:
            self._header()
        self._print_attr()
        # start monitoring for bad attribute
        self._set_attr_err = True

    def _get_config_path(self):
        """get the config path"""
        # cli provided
        if self.args['--cfg']:
            return os.path.expanduser(self.args['--cfg'])

        # environment variable provided
        if ENV_CONFIG in os.environ:
            return os.path.expanduser(os.environ[ENV_CONFIG])

        # look in current directory
        if os.path.exists(CONFIG):
            return CONFIG

        # look in XDG_CONFIG_HOME
        if ENV_XDG in os.environ:
            cfg = os.path.expanduser(os.environ[ENV_XDG])
            path = os.path.join(cfg, NAME, CONFIG)
            if os.path.exists(path):
                return path

        # look in ~/.config/dotdrop
        cfg = os.path.expanduser(HOMECFG)
        path = os.path.join(cfg, CONFIG)
        if os.path.exists(path):
            return path

        # look in /etc/xdg/dotdrop
        path = os.path.join(ETCXDGCFG, CONFIG)
        if os.path.exists(path):
            return path

        # look in /etc/dotdrop
        path = os.path.join(ETCCFG, CONFIG)
        if os.path.exists(path):
            return path

        return None

    def _find_cfg(self, paths):
        """try to find the config in the paths list"""
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _header(self):
        """print the header"""
        self.log.log(BANNER)
        self.log.log('')

    def _read_config(self, profile=None):
        """read the config file"""
        self.conf = Cfg(self.confpath, profile=profile, debug=self.debug)
        # transform the config settings to self attribute
        for k, v in self.conf.get_settings().items():
            if self.debug:
                self.log.dbg('setting: {}={}'.format(k, v))
            setattr(self, k, v)

    def _apply_args(self):
        """apply cli args as attribute"""
        # the commands
        self.cmd_list = self.args['list']
        self.cmd_listfiles = self.args['listfiles']
        self.cmd_install = self.args['install']
        self.cmd_compare = self.args['compare']
        self.cmd_import = self.args['import']
        self.cmd_update = self.args['update']
        self.cmd_detail = self.args['detail']

        # adapt attributes based on arguments
        self.dry = self.args['--dry']
        self.safe = not self.args['--force']

        # import link default value
        self.import_link = self.link_on_import
        if self.args['--link']:
            # overwrite default import link with cli switch
            link = self.args['--link']
            if link not in OPT_LINK.keys():
                self.log.err('bad option for --link: {}'.format(link))
                sys.exit(USAGE)
            self.import_link = OPT_LINK[link]
        if self.debug:
            self.log.dbg('link_import value: {}'.format(self.import_link))

        # "listfiles" specifics
        self.listfiles_templateonly = self.args['--template']
        # "install" specifics
        self.install_temporary = self.args['--temp']
        self.install_keys = self.args['<key>']
        self.install_diff = not self.args['--nodiff']
        self.install_showdiff = self.showdiff or self.args['--showdiff']
        self.install_backup_suffix = BACKUP_SUFFIX
        self.install_default_actions = self.default_actions
        # "compare" specifics
        self.compare_dopts = self.args['--dopts']
        self.compare_focus = self.args['--file']
        self.compare_ignore = self.args['--ignore']
        self.compare_ignore.append('*{}'.format(self.install_backup_suffix))
        # "import" specifics
        self.import_path = self.args['<path>']
        # "update" specifics
        self.update_path = self.args['<path>']
        self.update_iskey = self.args['--key']
        self.update_ignore = self.args['--ignore']
        self.update_ignore.append('*{}'.format(self.install_backup_suffix))
        self.update_showpatch = self.args['--show-patch']
        # "detail" specifics
        self.detail_keys = self.args['<key>']

    def _fill_attr(self):
        """create attributes from conf"""
        # variables
        self.variables = self.conf.get_variables(self.profile,
                                                 debug=self.debug).copy()
        # the dotfiles
        self.dotfiles = self.conf.eval_dotfiles(self.profile, self.variables,
                                                debug=self.debug).copy()
        # the profiles
        self.profiles = self.conf.get_profiles()

    def _print_attr(self):
        """print all of this class attributes"""
        if not self.debug:
            return
        self.log.dbg('options:')
        for att in dir(self):
            if att.startswith('_'):
                continue
            val = getattr(self, att)
            if callable(val):
                continue
            self.log.dbg('- {}: \"{}\"'.format(att, val))

    def _attr_set(self, attr):
        """error when some inexistent attr is set"""
        raise Exception('bad option: {}'.format(attr))
