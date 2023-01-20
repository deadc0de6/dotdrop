#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2020, deadc0de6

tests launcher
"""


import os
import sys
import subprocess
from concurrent import futures
from halo import Halo


LOG_FILE = '/tmp/dotdrop-tests-launcher.log'


def is_cicd():
    """are we in a CICD env (github actions)"""
    return 'GITHUB_WORKFLOW' in os.environ


def run_test(logfd, path):
    """run test pointed by path"""
    cur = os.path.dirname(sys.argv[0])
    name = os.path.basename(path)
    path = os.path.join(cur, name)

    if logfd:
        logfd.write(f'starting test \"{path}\"\n')
        logfd.flush()
    proc = subprocess.Popen(path, shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    out, _ = proc.communicate()
    ret = proc.returncode == 0
    reason = 'returncode'
    if 'Traceback' in out:
        ret = False
        reason = 'traceback'
    if logfd:
        logfd.write(f'done test \"{path}\": ok:{ret}\n')
        logfd.flush()
    return ret, reason, path, out


def get_tests():
    """get all tests available in current directory"""
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
    """entry point"""
    max_jobs = None  # number of processor
    if len(sys.argv) > 1:
        max_jobs = int(sys.argv[1])

    tests = get_tests()

    logfd = sys.stdout
    if not is_cicd():
        logfd = open(LOG_FILE, 'w', encoding='utf-8')
    if max_jobs:
        logfd.write(f'start with {max_jobs} parallel worker(s)\n')
    logfd.write(f'running {len(tests)} test(s)\n')
    logfd.flush()

    print()
    spinner = None
    if not is_cicd():
        # no spinner on github actions
        spinner = Halo(text='Testing', spinner='bouncingBall')
        spinner.start()
    with futures.ThreadPoolExecutor(max_workers=max_jobs) as ex:
        wait_for = []
        for test in tests:
            j = ex.submit(run_test, logfd, test)
            wait_for.append(j)
        logfd.flush()

        for test in futures.as_completed(wait_for):
            ret, reason, name, log = test.result()
            logfd.flush()
            if not ret:
                ex.shutdown(wait=False)
                for remainer in wait_for:
                    remainer.cancel()
                print()
                print(log)
                print(f'test \"{name}\" failed: {reason}')
                logfd.close()
                return False
        sys.stdout.write('\n')
    if spinner:
        spinner.stop()
    print()
    logfd.write(f'done - ran {len(tests)} test(s)\n')
    logfd.close()
    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
    sys.exit(0)
