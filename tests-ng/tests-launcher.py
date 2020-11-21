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


MAX_JOBS = 10


def run_test(path):
    cur = os.path.dirname(sys.argv[0])
    name = os.path.basename(path)
    path = os.path.join(cur, name)

    p = subprocess.Popen(path, shell=False,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    out, _ = p.communicate()
    out = out.decode()
    r = p.returncode == 0
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

    with futures.ThreadPoolExecutor(max_workers=MAX_JOBS) as ex:
        wait_for = []
        for test in tests:
            j = ex.submit(run_test, test)
            wait_for.append(j)

        for f in futures.as_completed(wait_for):
            r, reason, p, log = f.result()
            if not r:
                ex.shutdown(wait=False)
                for x in wait_for:
                    x.cancel()
                print()
                print(log)
                print('test {} failed ({})'.format(p, reason))
                return False
            else:
                sys.stdout.write('.')
                sys.stdout.flush()
        sys.stdout.write('\n')
    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
    sys.exit(0)
