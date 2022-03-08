#!/usr/bin/env python3

from ruamel.yaml import YAML as yaml
from deepdiff import DeepDiff
import toml
import os
import sys
import pprint
import json

# pip install toml deepdiff


def _yaml_load(path):
    """load from yaml"""
    with open(path, 'r', encoding='utf8') as file:
        data = yaml()
        data.typ = 'rt'
        content = data.load(file)
    return content


def _yaml_dump(content, where):
    """dump to yaml"""
    data = yaml()
    data.default_flow_style = False
    data.indent = 2
    data.typ = 'rt'
    data.dump(content, where)


def _toml_load(path):
    """load from toml"""
    with open(path, 'r', encoding='utf8') as file:
        data = file.read()
    content = toml.loads(data)
    return content


def _toml_dump(content, where):
    with open(where, 'w') as f:
        toml.dump(content, f)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("usage:")
        print(" {} to-toml <yaml-path>".format(sys.argv[0]))
        print(" {} to-yaml <toml-path>".format(sys.argv[0]))
        print(" {} compare <yaml-path> <toml-path>".format(sys.argv[0]))
        sys.exit(1)

    act = sys.argv[1]
    arg = sys.argv[2]
    if len(sys.argv) > 3:
        arg2 = sys.argv[3]
    out = '/tmp/res'

    if act == "to-toml":

        content = _yaml_load(arg)
        o = out + '.toml'
        _toml_dump(content, o)
        print("saved to {}".format(o))

    elif act == "to-yaml":

        content = _toml_load(arg)
        o = out + '.yaml'
        _yaml_dump(content, o)
        print("saved to {}".format(o))

    elif act == "compare":
        a = _yaml_load(arg)

        print("YAML dict:")
        print(json.dumps(a, indent=4))
        b = _toml_load(arg2)

        print("TOML dict:")
        print(json.dumps(b, indent=4))

        diff = DeepDiff(a, b, ignore_order=True, view='tree')
        print(diff)
