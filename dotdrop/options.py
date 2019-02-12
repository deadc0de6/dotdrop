"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

stores all options to use across dotdrop
"""

import os
import socket
from docopt import docopt

# local imports
from dotdrop.version import __version__ as VERSION
from dotdrop.linktypes import LinkTypes
from dotdrop.logger import Logger
from dotdrop.config import Cfg


PROFILE = socket.gethostname()
ENV_PROFILE = 'DOTDROP_PROFILE'
ENV_NOBANNER = 'DOTDROP_NOBANNER'
if ENV_PROFILE in os.environ:
    PROFILE = os.environ[ENV_PROFILE]

BANNER = """     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v{}
                               |_|""".format(VERSION)

USAGE = """
{}

Usage:
  dotdrop install   [-VbtfndD] [-c <path>] [-p <profile>] [<key>...]
  dotdrop import    [-Vbld]    [-c <path>] [-p <profile>] <path>...
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
  -c --cfg=<path>         Path to the config [default: config.yaml].
  -C --file=<path>        Path of dotfile to compare.
  -i --ignore=<pattern>   Pattern to ignore.
  -o --dopts=<opts>       Diff options [default: ].
  -n --nodiff             Do not diff when installing.
  -t --temp               Install to a temporary directory for review.
  -T --template           Only template dotfiles.
  -D --showdiff           Show a diff before overwriting.
  -l --inv-link           Invert the value of "link_by_default" when importing.
  -P --show-patch         Provide a one-liner to manually patch template.
  -f --force              Do not warn if exists.
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
        self.confpath = os.path.expanduser(self.args['--cfg'])
        if self.debug:
            self.log.dbg('config file: {}'.format(self.confpath))

        self._read_config()
        self._apply_args()
        self._fill_attr()
        if ENV_NOBANNER not in os.environ \
           and self.banner \
           and not self.args['--no-banner']:
            self._header()
        self._print_attr()
        # start monitoring for bad attribute
        self._set_attr_err = True

    def _header(self):
        """print the header"""
        self.log.log(BANNER)
        self.log.log('')

    def _read_config(self):
        """read the config file"""
        self.conf = Cfg(self.confpath, debug=self.debug)
        # transform the configs in attribute
        for k, v in self.conf.get_settings().items():
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
        self.profile = self.args['--profile']
        self.safe = not self.args['--force']
        self.link = LinkTypes.NOLINK
        if self.link_by_default:
            self.link = LinkTypes.PARENTS

        if self.args['--inv-link']:
            # Only invert link type from NOLINK to PARENTS and vice-versa
            if self.link == LinkTypes.NOLINK:
                self.link = LinkTypes.PARENTS
            elif self.link == LinkTypes.PARENTS:
                self.link = LinkTypes.NOLINK

        # "listfiles" specifics
        self.listfiles_templateonly = self.args['--template']
        # "install" specifics
        self.install_temporary = self.args['--temp']
        self.install_keys = self.args['<key>']
        self.install_diff = not self.args['--nodiff']
        self.install_showdiff = self.showdiff or self.args['--showdiff']
        # "compare" specifics
        self.compare_dopts = self.args['--dopts']
        self.compare_focus = self.args['--file']
        self.compare_ignore = self.args['--ignore']
        # "import" specifics
        self.import_path = self.args['<path>']
        # "update" specifics
        self.update_path = self.args['<path>']
        self.update_iskey = self.args['--key']
        self.update_ignore = self.args['--ignore']
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
