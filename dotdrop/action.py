"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

represent an action or transformation
in dotdrop
"""

import subprocess
import os

# local imports
from dotdrop.logger import Logger
from dotdrop.utils import DictParser


class Cmd:
    eq_ignore = ('log',)

    def __init__(self, key, action):
        """constructor
        @key: action key
        @action: action string
        """
        self.key = key
        self.action = action
        self.log = Logger()

    def __str__(self):
        return 'key:{} -> \"{}\"'.format(self.key, self.action)

    def __repr__(self):
        return 'cmd({})'.format(self.__str__())

    def __eq__(self, other):
        self_dict = {
            k: v
            for k, v in self.__dict__.items()
            if k not in self.eq_ignore
        }
        other_dict = {
            k: v
            for k, v in other.__dict__.items()
            if k not in self.eq_ignore
        }
        return self_dict == other_dict

    def __hash__(self):
        return hash(self.key) ^ hash(self.action)


class Action(Cmd, DictParser):

    def __init__(self, key, kind, action, *args):
        """constructor
        @key: action key
        @kind: type of action (pre or post)
        @action: action string
        @args: action arguments
        """
        super(Action, self).__init__(key, action)
        self.kind = kind
        self.args = args

    def __str__(self):
        out = '{}: \"{}\" with args: {}'
        return out.format(self.key, self.action, self.args)

    def __repr__(self):
        return 'action({})'.format(self.__str__())

    def execute(self, templater=None):
        """execute the action in the shell"""
        ret = 1
        action = self.action
        if templater:
            action = templater.generate_string(self.action)
        try:
            cmd = action.format(*self.args)
        except IndexError:
            err = 'bad action: \"{}\"'.format(action)
            err += ' with \"{}\"'.format(self.args)
            self.log.warn(err)
            return False
        self.log.sub('executing \"{}\"'.format(cmd))
        try:
            ret = subprocess.call(cmd, shell=True)
        except KeyboardInterrupt:
            self.log.warn('action interrupted')
        if ret != 0:
            self.log.warn('action returned code {}'.format(ret))
        return ret == 0


class Transform(Cmd, DictParser):

    def transform(self, arg0, arg1):
        """execute transformation with {0} and {1}
        where {0} is the file to transform and
        {1} is the result file"""
        ret = 1
        cmd = self.action.format(arg0, arg1)
        if os.path.exists(arg1):
            msg = 'transformation \"{}\": destination exists: {}'
            self.log.warn(msg.format(cmd, arg1))
            return False
        self.log.sub('transforming with \"{}\"'.format(cmd))
        try:
            ret = subprocess.call(cmd, shell=True)
        except KeyboardInterrupt:
            self.log.warn('transformation interrupted')
        if ret != 0:
            self.log.warn('transformation returned code {}'.format(ret))
        return ret == 0
