"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

settings block
"""

# local imports
from dotdrop.linktypes import LinkTypes
from dotdrop.dictparser import DictParser


class Settings(DictParser):
    # key in yaml file
    key_yaml = 'config'

    # settings item keys
    key_backup = 'backup'
    key_banner = 'banner'
    key_create = 'create'
    key_default_actions = 'default_actions'
    key_dotpath = 'dotpath'
    key_ignoreempty = 'ignoreempty'
    key_keepdot = 'keepdot'
    key_longkey = 'longkey'
    key_link_dotfile_default = 'link_dotfile_default'
    key_link_on_import = 'link_on_import'
    key_showdiff = 'showdiff'
    key_upignore = 'upignore'
    key_cmpignore = 'cmpignore'
    key_instignore = 'instignore'
    key_workdir = 'workdir'
    key_minversion = 'minversion'
    key_func_file = 'func_file'
    key_filter_file = 'filter_file'
    key_diff_command = 'diff_command'
    key_template_dotfile_default = 'template_dotfile_default'

    # import keys
    key_import_actions = 'import_actions'
    key_import_configs = 'import_configs'
    key_import_variables = 'import_variables'

    def __init__(self, backup=True, banner=True,
                 create=True, default_actions=[], dotpath='dotfiles',
                 ignoreempty=True, import_actions=[], import_configs=[],
                 import_variables=[], keepdot=False,
                 link_dotfile_default=LinkTypes.NOLINK,
                 link_on_import=LinkTypes.NOLINK, longkey=False,
                 upignore=[], cmpignore=[], instignore=[],
                 workdir='~/.config/dotdrop', showdiff=False,
                 minversion=None, func_file=[], filter_file=[],
                 diff_command='diff -r -u {0} {1}',
                 template_dotfile_default=True):
        self.backup = backup
        self.banner = banner
        self.create = create
        self.default_actions = default_actions
        self.dotpath = dotpath
        self.ignoreempty = ignoreempty
        self.import_actions = import_actions
        self.import_configs = import_configs
        self.import_variables = import_variables
        self.keepdot = keepdot
        self.longkey = longkey
        self.showdiff = showdiff
        self.upignore = upignore
        self.cmpignore = cmpignore
        self.instignore = instignore
        self.workdir = workdir
        self.link_dotfile_default = LinkTypes.get(link_dotfile_default)
        self.link_on_import = LinkTypes.get(link_on_import)
        self.minversion = minversion
        self.func_file = func_file
        self.filter_file = filter_file
        self.diff_command = diff_command
        self.template_dotfile_default = template_dotfile_default

    def _serialize_seq(self, name, dic):
        """serialize attribute 'name' into 'dic'"""
        seq = getattr(self, name)
        dic[name] = seq

    def serialize(self):
        """Return key-value pair representation of the settings"""
        dic = {
            self.key_backup: self.backup,
            self.key_banner: self.banner,
            self.key_create: self.create,
            self.key_dotpath: self.dotpath,
            self.key_ignoreempty: self.ignoreempty,
            self.key_keepdot: self.keepdot,
            self.key_link_dotfile_default: str(self.link_dotfile_default),
            self.key_link_on_import: str(self.link_on_import),
            self.key_longkey: self.longkey,
            self.key_showdiff: self.showdiff,
            self.key_workdir: self.workdir,
            self.key_minversion: self.minversion,
            self.key_diff_command: self.diff_command,
            self.key_template_dotfile_default: self.template_dotfile_default,
        }
        self._serialize_seq(self.key_default_actions, dic)
        self._serialize_seq(self.key_import_actions, dic)
        self._serialize_seq(self.key_import_configs, dic)
        self._serialize_seq(self.key_import_variables, dic)
        self._serialize_seq(self.key_cmpignore, dic)
        self._serialize_seq(self.key_upignore, dic)
        self._serialize_seq(self.key_instignore, dic)
        self._serialize_seq(self.key_func_file, dic)
        self._serialize_seq(self.key_filter_file, dic)

        return {self.key_yaml: dic}
