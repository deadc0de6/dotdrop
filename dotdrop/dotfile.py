"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
represents a dotfile in dotdrop
"""


class Dotfile:

    def __init__(self, key, dst, src):
        self.key = key # key of dotfile in the config
        self.dst = dst # where to install this dotfile
        self.src = src # stored dotfile in dotdrop

    def __str__(self):
        string = 'key:%s, src: %s, dst: %s' % (self.key,
                                               self.src, self.dst)
        return string
