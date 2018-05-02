"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
jinja2 template generator
"""

import os
from jinja2 import Environment, FileSystemLoader

# local imports
import dotdrop.utils as utils

BLOCK_START = '{%@@'
BLOCK_END = '@@%}'
VAR_START = '{{@@'
VAR_END = '@@}}'
COMMENT_START = '{#@@'
COMMENT_END = '@@#}'


class Templategen:

    def __init__(self, base='.'):
        self.base = base.rstrip(os.sep)
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

    def generate(self, src, profile):
        if not os.path.exists(src):
            return ''
        return self._handle_file(src, profile)

    def _handle_file(self, src, profile):
        """ generate the file content from template """
        filetype = utils.run(['file', '-b', src], raw=False)
        istext = 'text' in filetype
        if not istext:
            return self._handle_bin_file(src, profile)
        return self._handle_text_file(src, profile)

    def _handle_text_file(self, src, profile):
        template_rel_path = os.path.relpath(src, self.base)
        try:
            template = self.env.get_template(template_rel_path)
            content = template.render(profile=profile, env=os.environ)
        except UnicodeDecodeError:
            data = self._read_bad_encoded_text(src)
            template = self.env.from_string(data)
            content = template.render(profile=profile, env=os.environ)

        content = content.encode('UTF-8')
        return content

    def _handle_bin_file(self, src, profile):
        # this is dirty
        if not src.startswith(self.base):
            src = os.path.join(self.base, src)
        with open(src, 'rb') as f:
            return f.read()

    def _read_bad_encoded_text(self, path):
        with open(path, 'rb') as f:
            data = f.read()
        return data.decode('utf-8', 'replace')

    def get_marker():
        return BLOCK_START
