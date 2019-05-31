"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

dictionary parser abstract class
"""

from dotdrop.logger import Logger


class DictParser:

    log = Logger()

    @classmethod
    def _adjust_yaml_keys(cls, value):
        """adjust value for object 'cls'"""
        return value

    @classmethod
    def parse(cls, key, value):
        """parse (key,value) and construct object 'cls'"""
        tmp = value
        try:
            tmp = value.copy()
        except AttributeError:
            pass
        newv = cls._adjust_yaml_keys(tmp)
        if not key:
            return cls(**newv)
        return cls(key=key, **newv)

    @classmethod
    def parse_dict(cls, items):
        """parse a dictionary and construct object 'cls'"""
        if not items:
            return []
        return [cls.parse(k, v) for k, v in items.items()]
