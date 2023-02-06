"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2020, deadc0de6

represents a type of link in dotdrop
"""

# https://github.com/PyCQA/pylint/issues/2062
# pylint: disable=E1101

from enum import IntEnum


class LinkTypes(IntEnum):
    """a type of link"""
    NOLINK = 0
    LINK = 1
    LINK_CHILDREN = 2
    ABSOLUTE = 3
    RELATIVE = 4

    @classmethod
    def get(cls, key, default=None):
        """get the linktype"""
        try:
            return key if isinstance(key, cls) else cls[key.upper()]
        except KeyError as exc:
            if default and isinstance(default, cls):
                return default
            err = f'bad {cls.__name__} value: "{key}"'
            raise ValueError(err) from exc

    def __str__(self):
        """linktype to string"""
        return self.name.lower()
