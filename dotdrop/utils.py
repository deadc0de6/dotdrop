"""
author: deadc0de6 (https://github.com/deadc0de6)
utilities
"""

import subprocess
import tempfile
from logger import Logger

LOG = Logger()


def run(cmd, log=False, raw=True):
    """ expects a list """
    if log:
        LOG.log('cmd: \"%s\"' % (' '.join(cmd)))
    p = subprocess.Popen(cmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if raw:
        return p.stdout.readlines()
    return ''.join([x.decode('utf-8', 'replace') for x in p.stdout.readlines()])


def diff(src, dst, log=False, raw=True):
    return run(['diff', '-r', src, dst], log=log, raw=raw)


def get_tmpdir():
    return tempfile.mkdtemp(prefix='dotdrop-')
