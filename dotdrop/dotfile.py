"""
author: deadc0de6 (https://github.com/deadc0de6)
represents a dotfile in dotdrop
"""


class Dotfile:

    def __init__(self, key, dst, src):
        self.key = key
        self.dst = dst
        self.src = src

    def __str__(self):
        string = 'key:%s, src: %s, dst: %s' % (self.key,
                                               self.src, self.dst)
        return string
