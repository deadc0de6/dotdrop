#!/usr/bin/env python3
"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2022, deadc0de6

convert yaml config file to toml
"""

import sys
# pip3 install ruamel.yaml
from ruamel.yaml import YAML as yaml
# pip3 install tomli_w
import tomli_w


def yaml_load(path):
    """load from yaml"""
    with open(path, 'r', encoding='utf8') as file:
        cont = yaml()
        cont.typ = 'rt'
        content = cont.load(file)
    return content


def replace_none(content):
    """replace any occurence of None with empty string"""
    new = {}
    for k in content:
        if content[k] is None:
            if k == 'dotfiles':
                continue
            if k == 'profiles':
                continue
            new[k] = ""
            continue
        if isinstance(content[k], dict):
            new[k] = replace_none(content[k])
            continue
        new[k] = content[k]
    return new


def toml_dump(content):
    """dump toml to stdout"""
    return tomli_w.dumps(content)


def main():
    """entry point"""
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <yaml-config-path>")
        sys.exit(1)

    data = yaml_load(sys.argv[1])
    data = replace_none(data)
    out = toml_dump(data)
    print(out)


if __name__ == '__main__':
    main()
