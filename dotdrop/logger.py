"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

provide logging functions
"""

import sys
import inspect


class Logger:
    """logging facility for dotdrop"""

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    LMAGENTA = '\033[35m'
    RESET = '\033[0m'
    EMPH = '\033[33m'
    BOLD = '\033[1m'

    def __init__(self, debug: bool = False):
        self.debug = debug

    def log(self, string: str,
            end: str = '\n', pre: str = '',
            bold: bool = False) -> None:
        """normal log"""
        cstart = self._color(self.BLUE)
        cend = self._color(self.RESET)
        if bold:
            bold = self._color(self.BOLD)
            fmt = f'{pre}{cstart}{bold}{string}{cend}'
            fmt += f'{end}{cend}'
        else:
            fmt = f'{pre}{cstart}{string}{end}{cend}'
        sys.stdout.write(fmt)

    def sub(self, string: str,
            end: str = '\n') -> None:
        """sub log"""
        cstart = self._color(self.BLUE)
        cend = self._color(self.RESET)
        sys.stdout.write(f'\t{cstart}->{cend} {string}{end}')

    def emph(self, string: str, stdout: bool = True) -> None:
        """emphasis log"""
        cstart = self._color(self.EMPH)
        cend = self._color(self.RESET)
        content = f'{cstart}{string}{cend}'
        if not stdout:
            sys.stderr.write(content)
        else:
            sys.stdout.write(content)

    def err(self, string: str, end: str = '\n') -> None:
        """error log"""
        cstart = self._color(self.RED)
        cend = self._color(self.RESET)
        msg = f'{string} {end}'
        sys.stderr.write(f'{cstart}[ERR] {msg}{cend}')

    def warn(self, string: str, end: str = '\n') -> None:
        """warning log"""
        cstart = self._color(self.YELLOW)
        cend = self._color(self.RESET)
        sys.stderr.write(f'{cstart}[WARN] {string} {end}{cend}')

    def dbg(self, string: str, force: bool = False) -> None:
        """debug log"""
        if not force and not self.debug:
            return
        frame = inspect.stack()[1]

        mod = inspect.getmodule(frame[0])
        mod_name = 'module?'
        if mod:
            mod_name = mod.__name__
        func = inspect.stack()[1][3]
        cstart = self._color(self.MAGENTA)
        cend = self._color(self.RESET)
        clight = self._color(self.LMAGENTA)
        bold = self._color(self.BOLD)
        line = f'{bold}{clight}[DEBUG][{mod_name}.{func}]'
        line += f'{cend}{cstart} {string}{cend}\n'
        sys.stderr.write(line)

    def dry(self, string: str, end: str = '\n') -> None:
        """dry run log"""
        cstart = self._color(self.GREEN)
        cend = self._color(self.RESET)
        sys.stdout.write(f'{cstart}[DRY] {string} {end}{cend}')

    @classmethod
    def raw(cls, string: str, end: str = '\n') -> None:
        """raw log"""
        sys.stdout.write(f'{string}{end}')

    def ask(self, query: str) -> bool:
        """ask user for confirmation"""
        cstart = self._color(self.BLUE)
        cend = self._color(self.RESET)
        question = query + ' [y/N] ? '
        qmsg = f'{cstart}{question}{cend}'
        resp = input(qmsg)
        return resp == 'y'

    @classmethod
    def _color(cls, col: str) -> str:
        """is color supported"""
        if not sys.stdout.isatty():
            return ''
        return col
