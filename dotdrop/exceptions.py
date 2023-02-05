"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

diverse exceptions
"""


class YamlException(Exception):
    """exception in CfgYaml"""


class ConfigException(Exception):
    """exception in config parsing/aggregation"""


class OptionsException(Exception):
    """dotdrop options exception"""


class UndefinedException(Exception):
    """exception in templating"""


class UnmetDependency(Exception):
    """unmet dependency"""
