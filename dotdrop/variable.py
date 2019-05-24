"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

represents (dyn-)variables
"""

from dotdrop.utils import DictParser


class Var(DictParser):
    """Represent a variable."""

    def __init__(self, key, value):
        """
        constructor
        @key: the key string
        @value: the variable content
        """
        self.key = key
        self.value = value

    @classmethod
    def _adjust_yaml_keys(cls, key, value):
        v = {}
        v['value'] = value
        return key, v


class Variable(Var):
    # key in yaml file
    key_yaml = 'variables'


class DynVariable(Var):
    # key in yaml file
    key_yaml = 'dynvariables'
