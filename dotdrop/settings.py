#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import IntEnum

from .utils import with_yaml_parser


class LinkTypes(IntEnum):

    NOLINK = 0
    LINK = 1
    LINK_CHILDREN = 2

    def __str__(self):
        return self.name.lower()


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

    @classmethod
    @with_yaml_parser
    def parse(cls, yaml_dict, file_name=None):
        try:
            settings = yaml_dict[cls.key_yaml]
        except KeyError:
            raise ValueError('malformed file {}: missing key {}'
                             .format(file_name, cls.key_yaml))

        return cls(**settings)

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

        self.link_dotfile_default = (
            link_dotfile_default
            if isinstance(link_dotfile_default, LinkTypes)
            else LinkTypes[link_dotfile_default.upper()]
        )
        self.link_on_import = (
            link_on_import
            if isinstance(link_dotfile_default, LinkTypes)
            else LinkTypes[link_on_import.upper()]
        )

    def _add_seq(self, dic, name):
        key_name = 'key_{}'.format(name)
        attr = getattr(self, name)

        if attr:
            dic[key_name] = attr

    def serialize(self):
        dic = {
            self.key_backup: self.backup,
            self.key_banner: self.banner,
            self.key_create: self.create,
            self.key_dotpath: self.dotpath,
            self.key_ignoreempty: self.ignoreempty,
            self.key_link_dotfile_default: str(self.link_dotfile_default),
            self.key_link_on_import: str(self.link_on_import),
            self.key_longkey: self.longkey,
            self.key_keepdot: self.keepdot,
            self.key_showdiff: self.showdiff,
            self.key_workdir: self.workdir,
        }

        self._add_seq(dic, 'cmpignore')
        self._add_seq(dic, 'default_actions')
        self._add_seq(dic, 'import_actions')
        self._add_seq(dic, 'import_configs')
        self._add_seq(dic, 'import_variables')
        self._add_seq(dic, 'upignore')

        return dic
