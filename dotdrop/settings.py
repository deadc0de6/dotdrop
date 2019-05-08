#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .linktypes import LinkTypes
from .logger import Logger
from .utils import with_yaml_parser


class Settings:
    # key in yaml file
    key_yaml = 'config'

    # settings item keys
    key_backup = 'backup'
    key_banner = 'banner'
    key_cmpignore = 'cmpignore'
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
    key_workdir = 'workdir'

    # import keys
    key_import_actions = 'import_actions'
    key_import_configs = 'import_configs'
    key_import_variables = 'import_variables'

    log = Logger()

    def __init__(self, backup=True, banner=True, cmpignore=(), create=True,
                 default_actions=(), dotpath='dotfiles', ignoreempty=True,
                 import_actions=(), import_configs=(), import_variables=(),
                 keepdot=False, link_dotfile_default=LinkTypes.NOLINK,
                 link_on_import=LinkTypes.NOLINK, longkey=False,
                 showdiff=False, upignore=(), workdir='~/.config/dotdrop'):
        self.backup = backup
        self.banner = banner
        self.create = create
        self.cmpignore = cmpignore
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
        self.workdir = workdir

        self._init_link('link_dotfile_default', link_dotfile_default)
        self._init_link('link_on_import', link_on_import)

    @classmethod
    @with_yaml_parser
    def parse(cls, yaml_dict, file_name=None):
        try:
            settings = yaml_dict[cls.key_yaml]
        except KeyError:
            cls.log.err('malformed file {}: missing key "{}"'
                        .format(file_name, cls.key_yaml), throw=ValueError)

        return cls(**settings)

    def _init_link(self, attr_name, link_value):
        try:
            attr_value = (
                link_value
                if isinstance(link_value, LinkTypes)
                else LinkTypes[link_value.upper()]
            )
            setattr(self, attr_name, attr_value)
        except KeyError:
            attr_key = getattr(self, 'key_{}'.format(attr_name))
            self.log.err('bad value for key "{}": {}'
                         .format(attr_key, link_value), throw=ValueError)
