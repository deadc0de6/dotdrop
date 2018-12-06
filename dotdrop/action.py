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


class Cmd:

    def __init__(self, key, action):
        self.key = key
        self.action = action
        self.log = Logger()

    def __str__(self):
        return 'key:{} -> \"{}\"'.format(self.key, self.action)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.key) ^ hash(self.action)


class Action(Cmd):

    def __init__(self, key, action, *args):
        super(Action, self).__init__(key, action)
        self.args = args

    def execute(self):
        """execute the action in the shell"""
        ret = 1
        try:
            cmd = self.action.format(*self.args)
        except IndexError:
            err = 'bad action: \"{}\"'.format(self.action)
            err += ' with \"{}\"'.format(self.args)
            self.log.warn(err)
            return False
        self.log.sub('executing \"{}\"'.format(cmd))
        try:
            ret = subprocess.call(cmd, shell=True)
        except KeyboardInterrupt:
            self.log.warn('action interrupted')
        return ret == 0


class Transform(Cmd):

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
        return ret == 0
