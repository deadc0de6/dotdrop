"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

represents a dotfile in dotdrop
"""

from .linktypes import LinkTypes
from .logger import Logger
from .utils import destructure_keyval, with_yaml_parser


class Dotfile:
    # key in yaml file
    key_yaml = 'dotfiles'

    # dotfile keys
    key_actions = 'actions'
    key_cmpignore = 'cmpignore'
    key_dst = 'dst'
    key_noempty = 'ignoreempty'
    key_link = 'link'
    key_link_children = 'link_children'
    key_src = 'src'
    key_trans_r = 'trans'
    key_trans_w = 'trans_write'
    key_upignore = 'upignore'

    log = Logger()

    def __init__(self, key, dst, src,
                 actions=None, trans_r=None, trans_w=None,
                 link=LinkTypes.NOLINK, cmpignore=(),
                 noempty=False, upignore=()):
        """constructor
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
        self.actions = actions or {}
        self.cmpignore = cmpignore
        self.dst = dst
        self.key = key
        self.link = LinkTypes.get(link)
        self.noempty = noempty
        self.src = src
        self.trans_r = trans_r
        self.trans_w = trans_w
        self.upignore = upignore

    @classmethod
    @destructure_keyval
    def parse(cls, key, value):
        value = value.copy()
        value['noempty'] = value.get(cls.key_noempty, False)
        value['trans_r'] = value.get(cls.key_trans_r)
        value['trans_w'] = value.get(cls.key_trans_w)
        try:
            del (value[cls.key_noempty], value[cls.key_trans_r],
                 value[cls.key_trans_w])
        except KeyError:
            pass

        return cls(key=key, **value)

    @classmethod
    @with_yaml_parser
    def parse_dict(cls, yaml_dict, file_name=None):
        try:
            dotfiles = yaml_dict[cls.key_yaml]
        except KeyError:
            cls.log.err('malformed file {}: missing key "{}"'
                        .format(file_name, cls.key_yaml), throw=ValueError)

        return list(map(cls.parse, dotfiles.items()))

    @classmethod
    def serialize_dict(cls, actions):
        return {
            cls.key_yaml: dict(map(cls.serialize, actions))
        }

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.dst) ^ hash(self.src) ^ hash(self.key)

    def __str__(self):
        msg = 'key:\"{}\", src:\"{}\", dst:\"{}\", link:\"{}\"'
        return msg.format(self.key, self.src, self.dst, self.link.name.lower())

    def __repr__(self):
        return 'dotfile({!s})'.format(self)

    def get_vars(self):
        """return this dotfile templating vars"""
        return {
            '_dotfile_abs_src': self.src,
            '_dotfile_abs_dst': self.dst,
            '_dotfile_key': self.key,
            '_dotfile_link': str(self.link),
        }

    def serialize(self, as_dic=False):
        """Return key-value pair representation of this dotfile."""
        # Tedious, but less error-prone than introspection
        dic = {
            self.key_actions: self.actions,
            self.key_cmpignore: self.cmpignore,
            self.key_dst: self.dst,
            self.key_link: str(self.link),
            self.key_noempty: self.noempty,
            self.key_src: self.src,
            self.key_trans_r: self.trans_r,
            self.key_trans_w: self.trans_w,
            self.key_upignore: self.upignore,
        }
        return {self.key: dic} if as_dic else (self.key, dic)
