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
from dotdrop.cfg_aggregator import CfgAggregator as Cfg
from dotdrop.action import Action
from dotdrop.utils import uniq_list
from dotdrop.exceptions import YamlException

ENV_PROFILE = 'DOTDROP_PROFILE'
ENV_CONFIG = 'DOTDROP_CONFIG'
ENV_NOBANNER = 'DOTDROP_NOBANNER'
ENV_DEBUG = 'DOTDROP_DEBUG'
ENV_NODEBUG = 'DOTDROP_FORCE_NODEBUG'
ENV_XDG = 'XDG_CONFIG_HOME'
ENV_WORKERS = 'DOTDROP_WORKERS'
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

BANNER = r"""     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v{}
                               |_|""".format(VERSION)

USAGE = """
{}

Usage:
  dotdrop install   [-VbtfndDa] [-c <path>] [-p <profile>]
                                [-w <nb>] [<key>...]
  dotdrop import    [-Vbdfm]    [-c <path>] [-p <profile>] [-s <path>]
                                [-l <link>] [-i <pattern>...] <path>...
  dotdrop compare   [-LVbz]     [-c <path>] [-p <profile>]
                                [-w <nb>] [-C <file>...] [-i <pattern>...]
  dotdrop update    [-VbfdkPz]  [-c <path>] [-p <profile>]
                                [-w <nb>] [-i <pattern>...] [<path>...]
  dotdrop remove    [-Vbfdk]    [-c <path>] [-p <profile>] [<path>...]
  dotdrop files     [-VbTG]     [-c <path>] [-p <profile>]
  dotdrop detail    [-Vb]       [-c <path>] [-p <profile>] [<key>...]
  dotdrop profiles  [-VbG]      [-c <path>]
  dotdrop --help
  dotdrop --version

Options:
  -a --force-actions      Execute all actions even if no dotfile is installed.
  -b --no-banner          Do not display the banner.
  -c --cfg=<path>         Path to the config.
  -C --file=<path>        Path of dotfile to compare.
  -z --ignore-missing     Ignore files in installed folders that are missing.
  -d --dry                Dry run.
  -D --showdiff           Show a diff before overwriting.
  -f --force              Do not ask user confirmation for anything.
  -G --grepable           Grepable output.
  -i --ignore=<pattern>   Pattern to ignore.
  -k --key                Treat <path> as a dotfile key.
  -l --link=<link>        Link option (nolink|link|link_children).
  -L --file-only          Do not show diff but only the files that differ.
  -m --preserve-mode      Insert a chmod entry in the dotfile with its mode.
  -n --nodiff             Do not diff when installing.
  -p --profile=<profile>  Specify the profile to use [default: {}].
  -P --show-patch         Provide a one-liner to manually patch template.
  -s --as=<path>          Import as a different path from actual path.
  -t --temp               Install to a temporary directory for review.
  -T --template           Only template dotfiles.
  -V --verbose            Be verbose.
  -w --workers=<nb>       Number of concurrent workers [default: 1].
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
        self.args = {}
        if not args:
            self.args = docopt(USAGE, version=VERSION)
        if args:
            self.args = args.copy()
        self.log = Logger()
        self.debug = self.args['--verbose'] or ENV_DEBUG in os.environ
        self.dry = self.args['--dry']
        if ENV_NODEBUG in os.environ:
            # force disabling debugs
            self.debug = False
        self.profile = self.args['--profile']
        self.confpath = self._get_config_path()
        if not self.confpath:
            raise YamlException('no config file found')
        if self.debug:
            self.log.dbg('#################################################')
            self.log.dbg('#################### DOTDROP ####################')
            self.log.dbg('#################################################')
            self.log.dbg('version: {}'.format(VERSION))
            self.log.dbg('command: {}'.format(' '.join(sys.argv)))
            self.log.dbg('config file: {}'.format(self.confpath))

        self._read_config()
        self._apply_args()
        self._fill_attr()
        if ENV_NOBANNER not in os.environ \
           and self.banner \
           and not self.args['--no-banner']:
            self._header()
        self._debug_attr()
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

        return ''

    def _header(self):
        """display the header"""
        self.log.log(BANNER)
        self.log.log('')

    def _read_config(self):
        """read the config file"""
        self.conf = Cfg(self.confpath, self.profile, debug=self.debug,
                        dry=self.dry)
        # transform the config settings to self attribute
        self._debug_dict('effective settings', self.conf.get_settings())
        for k, v in self.conf.get_settings().items():
            setattr(self, k, v)

    def _apply_args(self):
        """apply cli args as attribute"""
        # the commands
        self.cmd_profiles = self.args['profiles']
        self.cmd_files = self.args['files']
        self.cmd_install = self.args['install']
        self.cmd_compare = self.args['compare']
        self.cmd_import = self.args['import']
        self.cmd_update = self.args['update']
        self.cmd_detail = self.args['detail']
        self.cmd_remove = self.args['remove']

        # adapt attributes based on arguments
        self.safe = not self.args['--force']

        try:
            if ENV_WORKERS in os.environ:
                workers = int(os.environ[ENV_WORKERS])
            else:
                workers = int(self.args['--workers'])
            self.workers = workers
        except ValueError:
            self.log.err('bad option for --workers')
            sys.exit(USAGE)

        # import link default value
        self.import_link = self.link_on_import
        if self.args['--link']:
            # overwrite default import link with cli switch
            link = self.args['--link']
            if link not in OPT_LINK.keys():
                self.log.err('bad option for --link: {}'.format(link))
                sys.exit(USAGE)
            self.import_link = OPT_LINK[link]

        # "files" specifics
        self.files_templateonly = self.args['--template']
        self.files_grepable = self.args['--grepable']

        # "profiles" specifics
        self.profiles_grepable = self.args['--grepable']

        # "install" specifics
        self.install_force_action = self.args['--force-actions']
        self.install_temporary = self.args['--temp']
        self.install_keys = self.args['<key>']
        self.install_diff = not self.args['--nodiff']
        self.install_showdiff = self.showdiff or self.args['--showdiff']
        self.install_backup_suffix = BACKUP_SUFFIX
        self.install_default_actions_pre = [a for a in self.default_actions
                                            if a.kind == Action.pre]
        self.install_default_actions_post = [a for a in self.default_actions
                                             if a.kind == Action.post]
        self.install_ignore = self.instignore

        # "compare" specifics
        self.compare_focus = self.args['--file']
        self.compare_ignore = self.args['--ignore']
        self.compare_ignore.extend(self.cmpignore)
        self.compare_ignore.append('*{}'.format(self.install_backup_suffix))
        self.compare_ignore = uniq_list(self.compare_ignore)
        self.compare_fileonly = self.args['--file-only']
        self.ignore_missing_in_dotdrop = self.ignore_missing_in_dotdrop or \
            self.args['--ignore-missing']

        # "import" specifics
        self.import_path = self.args['<path>']
        self.import_as = self.args['--as']
        self.import_mode = self.args['--preserve-mode']
        self.import_ignore = self.args['--ignore']
        self.import_ignore.extend(self.impignore)
        self.import_ignore.append('*{}'.format(self.install_backup_suffix))
        self.import_ignore = uniq_list(self.import_ignore)

        # "update" specifics
        self.update_path = self.args['<path>']
        self.update_iskey = self.args['--key']
        self.update_ignore = self.args['--ignore']
        self.update_ignore.extend(self.upignore)
        self.update_ignore.append('*{}'.format(self.install_backup_suffix))
        self.update_ignore = uniq_list(self.update_ignore)
        self.update_showpatch = self.args['--show-patch']

        # "detail" specifics
        self.detail_keys = self.args['<key>']

        # "remove" specifics
        self.remove_path = self.args['<path>']
        self.remove_iskey = self.args['--key']

    def _fill_attr(self):
        """create attributes from conf"""
        # variables
        self.variables = self.conf.get_variables()
        # the dotfiles
        self.dotfiles = self.conf.get_dotfiles()
        # the profiles
        self.profiles = self.conf.get_profiles()

    def _debug_attr(self):
        """debug display all of this class attributes"""
        if not self.debug:
            return
        self.log.dbg('effective options:')
        for att in dir(self):
            if att.startswith('_'):
                continue
            val = getattr(self, att)
            if callable(val):
                continue
            if type(val) is list:
                self._debug_list('-> {}'.format(att), val)
            elif type(val) is dict:
                self._debug_dict('-> {}'.format(att), val)
            else:
                self.log.dbg('-> {}: {}'.format(att, val))

    def _attr_set(self, attr):
        """error when some inexistent attr is set"""
        raise Exception('bad option: {}'.format(attr))

    def _debug_list(self, title, elems):
        """pretty print list"""
        if not self.debug:
            return
        self.log.dbg('{}:'.format(title))
        for e in elems:
            self.log.dbg('\t- {}'.format(e))

    def _debug_dict(self, title, elems):
        """pretty print dict"""
        if not self.debug:
            return
        self.log.dbg('{}:'.format(title))
        for k, v in elems.items():
            if type(v) is list:
                self.log.dbg('\t- \"{}\":'.format(k))
                for i in v:
                    self.log.dbg('\t\t- {}'.format(i))
            else:
                self.log.dbg('\t- \"{}\": {}'.format(k, v))
