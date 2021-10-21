#!/usr/bin/env python3
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# tests launcher
#


import os
import sys
import subprocess
from concurrent import futures
from halo import Halo


MAX_JOBS = 10
LOG_FILE = '/tmp/dotdrop-tests-launcher.log'


def run_test(logfd, path):
    cur = os.path.dirname(sys.argv[0])
    name = os.path.basename(path)
    path = os.path.join(cur, name)

    if logfd:
        logfd.write('starting test {}\n'.format(path))
    p = subprocess.Popen(path, shell=False,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    out, _ = p.communicate()
    out = out.decode()
    r = p.returncode == 0
    if logfd:
        logfd.write('done test {}\n'.format(path))
    reason = 'returncode'
    if 'Traceback' in out:
        r = False
        reason = 'traceback'
    return r, reason, path, out


def get_tests():
    tests = []
    cur = os.path.dirname(sys.argv[0])
    for (_, _, filenames) in os.walk(cur):
        for path in filenames:
            if not path.endswith('.sh'):
                continue
            tests.append(path)
        break
    return tests


def main():
    global MAX_JOBS
    if len(sys.argv) > 1:
        MAX_JOBS = int(sys.argv[1])

    tests = get_tests()

    fd = open(LOG_FILE, 'w')
    fd.write('start with {} jobs\n'.format(MAX_JOBS))
    fd.flush()

    print()
    spinner = Halo(text='Testing', spinner='bouncingBall')
    spinner.start()
    with futures.ThreadPoolExecutor(max_workers=MAX_JOBS) as ex:
        wait_for = []
        for test in tests:
            j = ex.submit(run_test, fd, test)
            wait_for.append(j)
        fd.flush()

        for f in futures.as_completed(wait_for):
            r, reason, p, log = f.result()
            fd.flush()
            if not r:
                ex.shutdown(wait=False)
                for x in wait_for:
                    x.cancel()
                print()
                print(log)
                print('test {} failed ({})'.format(p, reason))
                fd.close()
                return False
            #else:
            #    sys.stdout.write('.')
            #    sys.stdout.flush()
        sys.stdout.write('\n')
    spinner.stop()
    print()
    fd.write('done with {} jobs\n'.format(MAX_JOBS))
    fd.close()
    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
    sys.exit(0)
