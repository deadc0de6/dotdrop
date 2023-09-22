#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2020, deadc0de6

tests launcher
"""


import os
import sys
import subprocess
import argparse
from concurrent import futures
from halo import Halo


GITHUB_ENV = 'GITHUB_WORKFLOW'


def is_cicd():
    """are we in a CICD env (github actions)"""
    return GITHUB_ENV in os.environ


def run_test(logfd, path):
    """run test pointed by path"""
    cur = os.path.dirname(sys.argv[0])
    name = os.path.basename(path)
    path = os.path.join(cur, name)

    if logfd:
        logfd.write(f'starting test \"{path}\"\n')
        logfd.flush()
    # pylint: disable=R1732
    proc = subprocess.Popen(path, shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True,
                            encoding='utf-8',
                            errors='ignore')
    out, err = proc.communicate()
    ret = proc.returncode == 0
    reason = 'returncode'
    if 'Traceback' in out:
        ret = False
        reason = 'traceback'
    if logfd:
        logfd.write(f'done test \"{path}\": ok:{ret}\n')
        logfd.flush()
    return ret, reason, path, (out, err)


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
    tests.sort()
    return tests


def run_tests(max_jobs=None, stop_on_first_err=True, with_spinner=True):
    """run the tests"""
    # pylint: disable=R0914,R0912
    print(f'max parallel jobs: {max_jobs}')
    print(f'stop on first error: {stop_on_first_err}')
    print(f'use spinner: {with_spinner}')
    tests = get_tests()
    print(f'running {len(tests)} test script(s)\n')
    print()

    failed = 0
    success = 0
    spinner = None
    logfd = sys.stdout
    if not is_cicd() and with_spinner:
        # no spinner on github actions
        spinner = Halo(text='Testing', spinner='bouncingBall')
        spinner.start()
        logfd = None
    with futures.ThreadPoolExecutor(max_workers=max_jobs) as ex:
        wait_for = {}
        for test in tests:
            j = ex.submit(run_test, logfd, test)
            wait_for[j] = test

        for test in futures.as_completed(wait_for.keys()):
            try:
                ret, reason, name, (log_out, log_err) = test.result()
            # pylint: disable=W0703
            except Exception as exc:
                failed += 1
                print()
                print(f'test \"{wait_for[test]}\" failed (exception): {exc}')
                if stop_on_first_err:
                    ex.shutdown(wait=False)
                    for job in wait_for:
                        job.cancel()
                if stop_on_first_err:
                    return False
            if not ret:
                failed += 1
                print()
                if stop_on_first_err:
                    if log_out:
                        print(log_out)
                    if log_err:
                        print(log_err)
                print(f'test \"{name}\" failed ({ret}): {reason}')
                if stop_on_first_err:
                    ex.shutdown(wait=False)
                    for job in wait_for:
                        job.cancel()
                    return False
            else:
                success += 1
        sys.stdout.write('\n')
    if spinner:
        spinner.stop()
    print()
    print(f'done - ran {len(tests)} test(s)\n')
    if not stop_on_first_err:
        print(f'{failed}/{failed+success} failed tests')
    return failed < 1


def main():
    """entry point"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--proc',
                        type=int)
    parser.add_argument('-s', '--stoponerr',
                        action='store_true')
    parser.add_argument('-n', '--nospinner',
                        action='store_true')
    args = parser.parse_args()
    return run_tests(max_jobs=args.proc,
                     stop_on_first_err=args.stoponerr,
                     with_spinner=not args.nospinner)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
    sys.exit(0)
