#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .logger import Logger
from .utils import DictParser


class Profile(DictParser):
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
    def _adjust_yaml_keys(cls, value):
        value['imported_dotfiles'] = value.get(cls.key_import, ())
        try:
            del value[cls.key_import]
        except KeyError:
            pass

        return value

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return (hash(self.key) ^ hash(tuple(self.dotfiles))
                ^ hash(tuple(self.included_profiles)))

    def __str__(self):
        msg = 'key:"{}"'
        return msg.format(self.key)

    def __repr__(self):
        return 'profile({!s})'.format(self)
