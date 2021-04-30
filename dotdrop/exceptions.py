"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

diverse exceptions
"""


class YamlException(Exception):
    """exception in CfgYaml"""


class UndefinedException(Exception):
    """exception in templating"""


class UnmetDependency(Exception):
    """unmet dependency"""
