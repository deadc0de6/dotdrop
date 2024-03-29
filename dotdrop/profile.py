"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

represent a profile in dotdrop
"""

from dotdrop.dictparser import DictParser
from dotdrop.action import Action


class Profile(DictParser):
    """dotdrop profile"""

    # profile keys
    key_include = 'include'
    key_import = 'import'

    def __init__(self, key, actions=None, dotfiles=None,
                 variables=None, dynvariables=None):
        """
        constructor
        @key: profile key
        @actions: list of action keys
        @dotfiles: list of dotfile keys
        @variables: list of variable keys
        @dynvariables: list of interpreted variable keys
        """
        self.key = key
        self.actions = actions or []
        self.dotfiles = dotfiles or []
        self.variables = variables or []
        self.dynvariables = dynvariables or []

    def get_pre_actions(self):
        """return all 'pre' actions"""
        return [a for a in self.actions if a.kind == Action.pre]

    def get_post_actions(self):
        """return all 'post' actions"""
        return [a for a in self.actions if a.kind == Action.post]

    @classmethod
    def _adjust_yaml_keys(cls, value):
        """patch dict"""
        value.pop(cls.key_import, None)
        value.pop(cls.key_include, None)
        return value

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return (hash(self.key) ^
                hash(tuple(self.dotfiles)))

    def __str__(self):
        return f'key:"{self.key}"'

    def __repr__(self):
        return f'profile({self})'
