#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .logger import Logger
from .utils import destructure_keyval, with_yaml_parser


class Profile:
    """Represent a profile."""
    # key in yaml file
    key_yaml = 'profiles'

    # profile keys
    key_dotfiles = 'dotfiles'
    key_include = 'include'
    key_import = 'import'
    key_variables = 'variables'
    key_dynvariables = 'dynvariables'

    log = Logger()

    def __init__(self, key, dotfiles=None, imported_dotfiles=(), include=(),
                 variables=None, dynvariables=None):
        self.dotfiles = dotfiles or []
        self.key = key
        self.imported_dotfiles = imported_dotfiles
        self.included_profiles = include
        self.variables = variables or {}
        self.dynvariables = dynvariables or {}

    @classmethod
    @destructure_keyval
    def parse(cls, key, value):
        value = value.copy()
        value['imported_dotfiles'] = value.get(cls.key_import, ())
        try:
            del value[cls.key_import]
        except KeyError:
            pass

        return cls(key=key, **value)

    @classmethod
    @with_yaml_parser
    def parse_dict(cls, yaml_dict, file_name=None):
        try:
            profiles = yaml_dict[cls.key_yaml]
        except KeyError:
            cls.log.err('malformed file {}: missing key "{}"'
                        .format(file_name, cls.key_yaml), throw=ValueError)

        return list(map(cls.parse, profiles.items()))

    def __eq__(self, other):
        if isinstance(other, str):
            return self.key == other
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return (hash(self.key) ^ hash(tuple(self.dotfiles))
                ^ hash(tuple(self.included_profiles)))

    def __str__(self):
        msg = 'key:"{}"'
        return msg.format(self.key)

    def __repr__(self):
        return 'profile({!s})'.format(self)
