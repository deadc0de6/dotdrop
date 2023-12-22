"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

stores all options to use across dotdrop
"""

# attribute-defined-outside-init
# pylint: disable=W0201

import os
import sys
import socket
from docopt import docopt

# local imports
from dotdrop.version import __version__ as VERSION
from dotdrop.linktypes import LinkTypes
from dotdrop.logger import Logger
from dotdrop.cfg_aggregator import CfgAggregator
from dotdrop.action import Action
from dotdrop.utils import uniq_list, debug_list, debug_dict
from dotdrop.exceptions import YamlException, OptionsException

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
CONFIGFILEYAML = 'config.yaml'
CONFIGFILETOML = 'config.toml'
HOMECFG = f'~/.config/{NAME}'
ETCXDGCFG = f'/etc/xdg/{NAME}'
ETCCFG = f'/etc/{NAME}'

OPT_LINK = {
    LinkTypes.NOLINK.name.lower(): LinkTypes.NOLINK,
    LinkTypes.ABSOLUTE.name.lower(): LinkTypes.ABSOLUTE,
    LinkTypes.RELATIVE.name.lower(): LinkTypes.RELATIVE,
    LinkTypes.LINK_CHILDREN.name.lower(): LinkTypes.LINK_CHILDREN}

BANNER = fr"""     _       _      _
  __| | ___ | |_ __| |_ __ ___  _ __
 / _` |/ _ \| __/ _` | '__/ _ \| '_ |
 \__,_|\___/ \__\__,_|_|  \___/| .__/  v{VERSION}
                               |_|"""

USAGE = f"""
{BANNER}

Usage:
  dotdrop install   [-VbtfndDaWR] [-c <path>] [-p <profile>]
                                  [-w <nb>] [<key>...]
  dotdrop import    [-Vbdfm]      [-c <path>] [-p <profile>] [-i <pattern>...]
                                  [--transr=<key>] [--transw=<key>]
                                  [-l <link>] [-s <path>] <path>...
  dotdrop compare   [-LVbz]       [-c <path>] [-p <profile>]
                                  [-w <nb>] [-C <file>...] [-i <pattern>...]
  dotdrop update    [-VbfdkPz]    [-c <path>] [-p <profile>]
                                  [-w <nb>] [-i <pattern>...] [<path>...]
  dotdrop remove    [-Vbfdk]      [-c <path>] [-p <profile>] [<path>...]
  dotdrop uninstall [-Vbfd]       [-c <path>] [-p <profile>] [<key>...]
  dotdrop files     [-VbTG]       [-c <path>] [-p <profile>]
  dotdrop detail    [-Vb]         [-c <path>] [-p <profile>] [<key>...]
  dotdrop profiles  [-VbG]        [-c <path>]
  dotdrop --help
  dotdrop --version

Options:
  -a --force-actions      Execute all actions even if no dotfile is installed.
  -b --no-banner          Do not display the banner.
  -c --cfg=<path>         Path to the config.
  -C --file=<path>        Path of dotfile to compare.
  -d --dry                Dry run.
  -D --showdiff           Show a diff before overwriting.
  -f --force              Do not ask user confirmation for anything.
  -G --grepable           Grepable output.
  -i --ignore=<pattern>   Pattern to ignore.
  -k --key                Treat <path> as a dotfile key.
  -l --link=<link>        Link option (nolink|absolute|relative|link_children).
  -L --file-only          Do not show diff but only the files that differ.
  -m --preserve-mode      Insert a chmod entry in the dotfile with its mode.
  -n --nodiff             Do not diff when installing.
  -p --profile=<profile>  Specify the profile to use [default: {PROFILE}].
  -P --show-patch         Provide a one-liner to manually patch template.
  -R --remove-existing    Remove existing file on install directory.
  -s --as=<path>          Import as a different path from actual path.
  --transr=<key>          Associate trans_install key on import.
  --transw=<key>          Apply trans_update key on import.
  -t --temp               Install to a temporary directory for review.
  -T --template           Only template dotfiles.
  -V --verbose            Be verbose.
  -w --workers=<nb>       Number of concurrent workers [default: 1].
  -W --workdir-clear      Clear the workdir.
  -z --ignore-missing     Ignore files in installed folders that are missing.
  -v --version            Show version.
  -h --help               Show this screen.
"""


class AttrMonitor:
    """monitor attribute setter"""
    _set_attr_err = False

# pylint: disable=W0235
    def __setattr__(self, key, value):
        """monitor attribute setting"""
        super().__setattr__(key, value)
# pylint: enable=W0235

    def _attr_set(self, attr):
        """do something when unexistent attr is set"""


class Options(AttrMonitor):
    """dotdrop options manager"""

    def __init__(self, args=None):
        """constructor
        @args: argument dictionary (if None use sys)
        """
        # attributes gotten from self.conf.get_settings()
        self.banner = None
        self.showdiff = None
        self.default_actions = []
        self.instignore = None
        self.force_chmod = None
        self.cmpignore = None
        self.impignore = None
        self.upignore = None
        self.link_on_import = None
        self.chmod_on_import = None
        self.check_version = None
        self.clear_workdir = None
        self.key_prefix = None
        self.key_separator = None

        # args parsing
        self.args = {}
        if not args:
            self.args = docopt(USAGE, version=VERSION)
        if args:
            self.args = args.copy()
        self.debug = self.args['--verbose'] or ENV_DEBUG in os.environ
        self.log = Logger(debug=self.debug)
        self.dry = self.args['--dry']
        if ENV_NODEBUG in os.environ:
            # force disabling debugs
            self.debug = False
        # selected profile
        self.profile = self.args['--profile']
        self.confpath = self._get_config_path()
        self.confpath = os.path.abspath(self.confpath)
        self.log.dbg(f'config abs path: {self.confpath}')
        if not self.confpath:
            raise YamlException('no config file found')
        if not os.path.exists(self.confpath):
            err = f'bad config file path: {self.confpath}'
            raise YamlException(err)
        self.log.dbg('#################################################')
        self.log.dbg('#################### DOTDROP ####################')
        self.log.dbg('#################################################')
        self.log.dbg(f'version: {VERSION}')
        self.argv = ' '.join(sys.argv)
        self.log.dbg(f'command: {self.argv}')
        self.log.dbg(f'config file: {self.confpath}')

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

    def debug_command(self):
        """print the original command"""
        self.log.dbg(f'command: {self.argv}')

    @classmethod
    def _get_config_from_env(cls, name):
        # look in XDG_CONFIG_HOME
        if ENV_XDG in os.environ:
            cfg = os.path.expanduser(os.environ[ENV_XDG])
            path = os.path.join(cfg, NAME, name)
            if os.path.exists(path):
                return path
        return ''

    @classmethod
    def _get_config_from_fs(cls, name):
        """get config from filesystem"""
        # look in ~/.config/dotdrop
        cfg = os.path.expanduser(HOMECFG)
        path = os.path.join(cfg, name)
        if os.path.exists(path):
            return path

        # look in /etc/xdg/dotdrop
        path = os.path.join(ETCXDGCFG, name)
        if os.path.exists(path):
            return path

        # look in /etc/dotdrop
        path = os.path.join(ETCCFG, name)
        if os.path.exists(path):
            return path

        return ''

    def _get_config_path(self):
        """get the config path"""
        # cli provided
        if self.args['--cfg']:
            self.log.dbg(f'config from --cfg {self.args["--cfg"]}')
            return os.path.expanduser(self.args['--cfg'])

        # environment variable provided
        if ENV_CONFIG in os.environ:
            self.log.dbg(f'config from env {ENV_CONFIG}')
            return os.path.expanduser(os.environ[ENV_CONFIG])

        # look in current directory
        if os.path.exists(CONFIGFILEYAML):
            self.log.dbg(f'config from yaml in current dir {CONFIGFILEYAML}')
            return CONFIGFILEYAML

        # look in current directory
        if os.path.exists(CONFIGFILETOML):
            self.log.dbg(f'config from toml in current dir {CONFIGFILETOML}')
            return CONFIGFILETOML

        path = self._get_config_from_env(CONFIGFILEYAML)
        if path:
            self.log.dbg(f'config from env with {CONFIGFILEYAML}')
            return path

        path = self._get_config_from_env(CONFIGFILETOML)
        if path:
            self.log.dbg(f'config from env with {CONFIGFILETOML}')
            return path

        path = self._get_config_from_fs(CONFIGFILEYAML)
        if path:
            self.log.dbg(f'config from fs with {CONFIGFILEYAML}')
            return path

        path = self._get_config_from_fs(CONFIGFILETOML)
        if path:
            self.log.dbg(f'config from fs with {CONFIGFILETOML}')
            return path

        self.log.dbg('no config file found')
        return None

    def _header(self):
        """display the header"""
        self.log.log(BANNER)
        self.log.log('')

    def _read_config(self):
        """read the config file"""
        self.conf = CfgAggregator(self.confpath,
                                  self.profile,
                                  debug=self.debug,
                                  dry=self.dry)
        # transform the config settings to self attribute
        settings = self.conf.get_settings()
        debug_dict('effective settings', settings, self.debug)
        for k, val in settings.items():
            setattr(self, k, val)

    def _apply_args_files(self):
        """files specifics"""
        self.files_templateonly = self.args['--template']
        self.files_grepable = self.args['--grepable']

    def _apply_args_install(self):
        """install specifics"""
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
        self.install_force_chmod = self.force_chmod
        self.install_clear_workdir = self.args['--workdir-clear'] or \
            self.clear_workdir
        self.install_remove_existing = self.args['--remove-existing']

    def _apply_args_compare(self):
        """compare specifics"""
        self.compare_focus = self.args['--file']
        self.compare_ignore = self.args['--ignore']
        self.compare_ignore.extend(self.cmpignore)
        self.compare_ignore.append(f'*{self.install_backup_suffix}')
        self.compare_ignore = uniq_list(self.compare_ignore)
        self.compare_fileonly = self.args['--file-only']
        self.ignore_missing_in_dotdrop = self.ignore_missing_in_dotdrop or \
            self.args['--ignore-missing']

    def _apply_args_import(self):
        """import specifics"""
        self.import_path = self.args['<path>']
        self.import_as = self.args['--as']
        self.import_mode = self.args['--preserve-mode'] or self.chmod_on_import
        self.import_ignore = self.args['--ignore']
        self.import_ignore.extend(self.impignore)
        self.import_ignore.append(f'*{self.install_backup_suffix}')
        self.import_ignore = uniq_list(self.import_ignore)
        self.import_trans_install = self.args['--transr']
        self.import_trans_update = self.args['--transw']

    def _apply_args_update(self):
        """update specifics"""
        self.update_path = self.args['<path>']
        self.update_iskey = self.args['--key']
        self.update_ignore = self.args['--ignore']
        self.update_ignore.extend(self.upignore)
        self.update_ignore.append(f'*{self.install_backup_suffix}')
        self.update_ignore = uniq_list(self.update_ignore)
        self.update_showpatch = self.args['--show-patch']

    def _apply_args_profiles(self):
        """profiles specifics"""
        self.profiles_grepable = self.args['--grepable']

    def _apply_args_remove(self):
        """remove specifics"""
        self.remove_path = self.args['<path>']
        self.remove_iskey = self.args['--key']

    def _apply_args_uninstall(self):
        """uninstall specifics"""
        self.uninstall_key = self.args['<key>']

    def _apply_args_detail(self):
        """detail specifics"""
        self.detail_keys = self.args['<key>']

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
        self.cmd_uninstall = self.args['uninstall']

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
            if link not in OPT_LINK:
                self.log.err(f'bad option for --link: {link}')
                sys.exit(USAGE)
            self.import_link = OPT_LINK[link]

        # "files" specifics
        self._apply_args_files()

        # "install" specifics
        self._apply_args_install()

        # "compare" specifics
        self._apply_args_compare()

        # "import" specifics
        self._apply_args_import()

        # "update" specifics
        self._apply_args_update()

        # "profiles" specifics
        self._apply_args_profiles()

        # "detail" specifics
        self._apply_args_detail()

        # "remove" specifics
        self._apply_args_remove()

        # "uninstall" specifics
        self._apply_args_uninstall()

    def _fill_attr(self):
        """create attributes from conf"""
        # defined variables
        self.variables = self.conf.get_variables()
        # dotfiles for this profile
        self.dotfiles = self.conf.get_dotfiles(profile_key=self.profile)
        # all defined profiles
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
            if isinstance(val, list):
                debug_list(f'-> {att}', val, self.debug)
            elif isinstance(val, dict):
                debug_dict(f'-> {att}', val, self.debug)
            else:
                self.log.dbg(f'-> {att}: {val}')

    def _attr_set(self, attr):
        """error when some inexistent attr is set"""
        raise OptionsException(f'bad option: {attr}')
