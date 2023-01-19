#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

convert yaml config file to toml
"""

import sys
# pip3 install ruamel.yaml
from ruamel.yaml import YAML as yaml
# pip3 install toml
import toml


def yaml_load(path):
    """load from yaml"""
    with open(path, 'r', encoding='utf8') as file:
        cont = yaml()
        cont.typ = 'rt'
        content = cont.load(file)
    return content


def replace_none(content):
    """replace any occurence of None with empty string"""
    n = {}
    for k in content:
        if content[k] is None:
            if k == 'dotfiles':
                continue
            if k == 'profiles':
                continue
            n[k] = ""
            continue
        if isinstance(content[k], dict):
            n[k] = replace_none(content[k])
            continue
        n[k] = content[k]
    return n


def toml_dump(content):
    """dump toml to stdout"""
    return toml.dumps(content)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <yaml-config-path>")
        sys.exit(1)

    data = yaml_load(sys.argv[1])
    data = replace_none(data)
    out = toml_dump(data)
    print(out)
