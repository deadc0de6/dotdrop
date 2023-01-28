#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2023, deadc0de6

URL checking script
"""

import sys
import re
from urllib.parse import urlparse
import requests


RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

TIMEOUT = 3
VALID_RET = [
    200,
    302,
]
IGNORES = [
  'badgen.net',
]
IGNORE_GENERIC = [
    'assets/dotdrop.svg',
    'github.com/deadc0de6/dotdrop',
    'packages.debian.org',
]
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/58.0.3029.110 Safari/537.36'
)
HEADERS = {
    'User-Agent': USER_AGENT,
}
PATTERN = (
    r"https?://[a-zA-Z0-9][a-zA-Z0-9-]{1,61}"
    r"[a-zA-Z0-9]\.[=a-zA-Z0-9\_\/\?\&\%\+\#\.\-]+"
)


def get_links(path):
    """get a list of URLS"""
    with open(path, encoding='utf-8') as file:
        content = file.read()
    entries = re.findall(PATTERN, content)
    urls = list(set(entries))
    return urls


def check_links(urls):
    """check urls"""
    cnt = 0
    ign = 0
    for url in urls:
        cnt += 1
        ignored = False
        print(f'    checking {MAGENTA}{url}{RESET}')
        for ignore in IGNORE_GENERIC:
            if ignore in url:
                print(f'    {YELLOW}[IGN]{RESET} {url}')
                ign += 1
                ignored = True
                break
        if ignored:
            continue
        hostname = urlparse(url).hostname
        if hostname in IGNORES:
            print(f'    {YELLOW}[IGN]{RESET} {url}')
            ign += 1
            continue

        verb = 'head'
        try:
            ret = requests.head(url,
                                timeout=TIMEOUT,
                                allow_redirects=True,
                                headers=HEADERS).status_code
        # pylint: disable=W0703
        except Exception:
            ret = 404
        if ret not in VALID_RET:
            msg = (
                f'    {YELLOW}[WARN]{RESET} HEAD {url} returned {ret}'
                f' ... checking with GET'
            )
            print(msg)
            verb = 'get'
            ret = requests.get(url,
                               timeout=TIMEOUT,
                               allow_redirects=True,
                               headers=HEADERS).status_code
            if ret not in VALID_RET:
                print(f'    {RED}[ERROR]{RESET} {url} returned {ret}')
                return False
        print(f'    [{GREEN}OK{RESET}-{verb}-{ret}] {MAGENTA}{url}{RESET}')
    print(f'    {GREEN}OK{RESET} - total {cnt} links checked ({ign} ignored)')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'usage: {sys.argv[0]} <path>')
        sys.exit(1)

    print(f'checking {BLUE}{sys.argv[1]}{RESET} for links...')
    links = get_links(sys.argv[1])
    print(f'    found {len(links)} links')
    try:
        if not check_links(links):
            sys.exit(1)
    # pylint: disable=W0703
    except Exception as exc:
        print(f'error {exc}')
        sys.exit(1)
    sys.exit(0)
