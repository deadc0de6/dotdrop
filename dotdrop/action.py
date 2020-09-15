"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

represent an action or transformation
in dotdrop
"""

import subprocess
import os

# local imports
from dotdrop.dictparser import DictParser
from dotdrop.exceptions import UndefinedException


class Cmd(DictParser):
    eq_ignore = ('log',)
    descr = 'command'

    def __init__(self, key, action):
        """constructor
        @key: action key
        @action: action string
        @silent: action silent
        """
        self.key = key
        self.action = action
        self.silent = key.startswith('_')

    def execute(self, templater=None, debug=False):
        """execute the command in the shell"""
        ret = 1
        action = self.action
        if templater:
            try:
                action = templater.generate_string(self.action)
            except UndefinedException as e:
                err = 'bad {}: {}'.format(self.descr, e)
                self.log.warn(err)
                return False
            if debug:
                self.log.dbg('{}:'.format(self.descr))
                self.log.dbg('  - raw       \"{}\"'.format(self.action))
                self.log.dbg('  - templated \"{}\"'.format(action))
        cmd = action
        args = []
        if self.args:
            args = self.args
            if templater:
                try:
                    args = [templater.generate_string(a) for a in args]
                except UndefinedException as e:
                    err = 'bad arguments for {}: {}'.format(self.descr, e)
                    self.log.warn(err)
                    return False
        if debug and args:
            self.log.dbg('action args:')
            for cnt, arg in enumerate(args):
                self.log.dbg('\targs[{}]: {}'.format(cnt, arg))
        try:
            cmd = action.format(*args)
        except IndexError:
            err = 'bad {}: \"{}\"'.format(self.descr, action)
            err += ' with \"{}\"'.format(args)
            self.log.warn(err)
            return False
        except KeyError:
            err = 'bad {}: \"{}\"'.format(self.descr, action)
            err += ' with \"{}\"'.format(args)
            self.log.warn(err)
            return False
        if self.silent:
            self.log.sub('executing silent action \"{}\"'.format(self.key))
            if debug:
                self.log.dbg('action cmd silenced')
        else:
            if debug:
                self.log.dbg('action cmd: \"{}\"'.format(cmd))
            self.log.sub('executing \"{}\"'.format(cmd))
        try:
            ret = subprocess.call(cmd, shell=True)
        except KeyboardInterrupt:
            self.log.warn('{} interrupted'.format(self.descr))
        if ret != 0:
            self.log.warn('{} returned code {}'.format(self.descr, ret))
        return ret == 0

    @classmethod
    def _adjust_yaml_keys(cls, value):
        return {'action': value}

    def __str__(self):
        return 'key:{} -> \"{}\"'.format(self.key, self.action)


class Action(Cmd):

    pre = 'pre'
    post = 'post'
    descr = 'action'

    def __init__(self, key, kind, action):
        """constructor
        @key: action key
        @kind: type of action (pre or post)
        @action: action string
        """
        super(Action, self).__init__(key, action)
        self.kind = kind
        self.args = []

    def copy(self, args):
        """return a copy of this object with arguments"""
        action = Action(self.key, self.kind, self.action)
        action.args = args
        return action

    @classmethod
    def parse(cls, key, value):
        """parse key value into object"""
        v = {}
        v['kind'], v['action'] = value
        return cls(key=key, **v)

    def __str__(self):
        out = '{}: [{}] \"{}\"'
        return out.format(self.key, self.kind, self.action)

    def __repr__(self):
        return 'action({})'.format(self.__str__())


class Transform(Cmd):
    descr = 'transformation'

    def __init__(self, key, action):
        """constructor
        @key: action key
        @trans: action string
        """
        super(Transform, self).__init__(key, action)
        self.args = []

    def copy(self, args):
        """return a copy of this object with arguments"""
        trans = Transform(self.key, self.action)
        trans.args = args
        return trans

    def transform(self, arg0, arg1, templater=None, debug=False):
        """
        execute transformation with {0} and {1}
        where {0} is the file to transform
        and {1} is the result file
        """
        if os.path.exists(arg1):
            msg = 'transformation \"{}\": destination exists: {}'
            self.log.warn(msg.format(self.key, arg1))
            return False

        if not self.args:
            self.args = []
        self.args.insert(0, arg1)
        self.args.insert(0, arg0)
        return self.execute(templater=templater, debug=debug)
