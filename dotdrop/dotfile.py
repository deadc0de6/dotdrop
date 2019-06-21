"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

represents a dotfile in dotdrop
"""

from dotdrop.linktypes import LinkTypes
from dotdrop.dictparser import DictParser
from dotdrop.action import Action


class Dotfile(DictParser):
    """Represent a dotfile."""
    # dotfile keys
    key_noempty = 'ignoreempty'
    key_trans_r = 'trans_read'
    key_trans_w = 'trans_write'

    def __init__(self, key, dst, src,
                 actions=[], trans_r=None, trans_w=None,
                 link=LinkTypes.NOLINK, cmpignore=[],
                 noempty=False, upignore=[]):
        """
        constructor
        @key: dotfile key
        @dst: dotfile dst (in user's home usually)
        @src: dotfile src (in dotpath)
        @actions: dictionary of actions to execute for this dotfile
        @trans_r: transformation to change dotfile before it is installed
        @trans_w: transformation to change dotfile before updating it
        @link: link behavior
        @cmpignore: patterns to ignore when comparing
        @noempty: ignore empty template if True
        @upignore: patterns to ignore when updating
        """
        self.actions = actions
        self.cmpignore = cmpignore
        self.dst = dst
        self.key = key
        self.link = LinkTypes.get(link)
        self.noempty = noempty
        self.src = src
        self.trans_r = trans_r
        self.trans_w = trans_w
        self.upignore = upignore

        if self.link != LinkTypes.NOLINK and \
                (
                    (trans_r and len(trans_r) > 0)
                    or
                    (trans_w and len(trans_w) > 0)
                ):
            msg = '[{}] transformations disabled'.format(key)
            msg += ' because dotfile is linked'
            self.log.warn(msg)
            trans_r = []
            trans_w = []

    def get_dotfile_variables(self):
        """return this dotfile specific variables"""
        return {
            '_dotfile_abs_src': self.src,
            '_dotfile_abs_dst': self.dst,
            '_dotfile_key': self.key,
            '_dotfile_link': str(self.link),
        }

    def get_pre_actions(self):
        """return all 'pre' actions"""
        return [a for a in self.actions if a.kind == Action.pre]

    def get_post_actions(self):
        """return all 'post' actions"""
        return [a for a in self.actions if a.kind == Action.post]

    def get_trans_r(self):
        """return trans_r object"""
        return self.trans_r

    def get_trans_w(self):
        """return trans_w object"""
        return self.trans_w

    @classmethod
    def _adjust_yaml_keys(cls, value):
        """patch dict"""
        value['noempty'] = value.get(cls.key_noempty, False)
        value['trans_r'] = value.get(cls.key_trans_r)
        value['trans_w'] = value.get(cls.key_trans_w)
        # remove old entries
        value.pop(cls.key_noempty, None)
        value.pop(cls.key_trans_r, None)
        value.pop(cls.key_trans_w, None)
        return value

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.dst) ^ hash(self.src) ^ hash(self.key)

    def __str__(self):
        msg = 'key:\"{}\", src:\"{}\", dst:\"{}\", link:\"{}\"'
        return msg.format(self.key, self.src, self.dst, str(self.link))

    def __repr__(self):
        return 'dotfile({!s})'.format(self)
