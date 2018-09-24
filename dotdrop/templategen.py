"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

jinja2 template generator
"""

import os
from jinja2 import Environment, FileSystemLoader

# local imports
import dotdrop.utils as utils
from dotdrop.logger import Logger

BLOCK_START = '{%@@'
BLOCK_END = '@@%}'
VAR_START = '{{@@'
VAR_END = '@@}}'
COMMENT_START = '{#@@'
COMMENT_END = '@@#}'


class Templategen:

    def __init__(self, profile, base='.', variables={}, debug=False):
        self.base = base.rstrip(os.sep)
        self.debug = debug
        loader = FileSystemLoader(self.base)
        self.env = Environment(loader=loader,
                               trim_blocks=True, lstrip_blocks=True,
                               keep_trailing_newline=True,
                               block_start_string=BLOCK_START,
                               block_end_string=BLOCK_END,
                               variable_start_string=VAR_START,
                               variable_end_string=VAR_END,
                               comment_start_string=COMMENT_START,
                               comment_end_string=COMMENT_END)
        self.env.globals['header'] = self._header
        self.env.globals['env'] = os.environ
        self.env.globals['profile'] = profile
        self.env.globals.update(variables)
        self.log = Logger()

    def generate(self, src):
        if not os.path.exists(src):
            return ''
        return self._handle_file(src)

    def _header(self, prepend=''):
        """add a comment usually in the header of a dotfile"""
        return '{}{}'.format(prepend, utils.header())

    def _handle_file(self, src):
        """generate the file content from template"""
        filetype = utils.run(['file', '-b', src], raw=False, debug=self.debug)
        filetype = filetype.strip()
        if self.debug:
            self.log.dbg('\"{}\" filetype: {}'.format(src, filetype))
        istext = 'text' in filetype
        if self.debug:
            self.log.dbg('\"{}\" is text: {}'.format(src, istext))
        if not istext:
            return self._handle_bin_file(src)
        return self._handle_text_file(src)

    def _handle_text_file(self, src):
        """write text to file"""
        template_rel_path = os.path.relpath(src, self.base)
        try:
            template = self.env.get_template(template_rel_path)
            content = template.render()
        except UnicodeDecodeError:
            data = self._read_bad_encoded_text(src)
            template = self.env.from_string(data)
            content = template.render()

        content = content.encode('UTF-8')
        return content

    def _handle_bin_file(self, src):
        """write binary to file"""
        # this is dirty
        if not src.startswith(self.base):
            src = os.path.join(self.base, src)
        with open(src, 'rb') as f:
            return f.read()

    def _read_bad_encoded_text(self, path):
        """decode non utf-8 data"""
        with open(path, 'rb') as f:
            data = f.read()
        return data.decode('utf-8', 'replace')

    def is_template(path):
        """recursively check if any file is a template within path"""
        if not os.path.exists(path):
            return False
        if os.path.isfile(path):
            # is file
            return Templategen._is_template(path)
        for entry in os.listdir(path):
            fpath = os.path.join(path, entry)
            if not os.path.isfile(fpath):
                # rec explore dir
                if Templategen.is_template(fpath):
                    return True
            else:
                # is file a template
                if Templategen._is_template(fpath):
                    return True
        return False

    def _is_template(path):
        """test if file pointed by path is a template"""
        if not os.path.isfile(path):
            return False
        try:
            with open(path, 'r') as f:
                data = f.read()
        except UnicodeDecodeError:
            # is binary so surely no template
            return False
        markers = [BLOCK_START, VAR_START, COMMENT_START]
        for marker in markers:
            if marker in data:
                return True
        return False
