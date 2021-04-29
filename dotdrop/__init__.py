"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
"""

import sys
import dotdrop.dotdrop


def main():
    """entry point"""
    if dotdrop.dotdrop.main():
        sys.exit(0)
    sys.exit(1)
