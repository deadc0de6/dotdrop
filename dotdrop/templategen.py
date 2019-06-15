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
import dotdrop.jhelpers as jhelpers

BLOCK_START = '{%@@'
BLOCK_END = '@@%}'
VAR_START = '{{@@'
VAR_END = '@@}}'
COMMENT_START = '{#@@'
COMMENT_END = '@@#}'


class Templategen:

    def __init__(self, base='.', variables={}, debug=False):
        """constructor
        @base: directory path where to search for templates
        @variables: dictionary of variables for templates
        @debug: enable debug
        """
        self.base = base.rstrip(os.sep)
        self.debug = debug
        self.log = Logger()
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
        # adding variables
        self.env.globals['env'] = os.environ
        if variables:
            self.env.globals.update(variables)
        # adding header method
        self.env.globals['header'] = self._header
        # adding helper methods
        self.env.globals['exists'] = jhelpers.exists
        self.env.globals['exists_in_path'] = jhelpers.exists_in_path
        self.env.globals['basename'] = jhelpers.basename
        self.env.globals['dirname'] = jhelpers.dirname
        if self.debug:
            self.log.dbg('template additional variables: {}'.format(variables))

    def generate(self, src):
        """render template from path"""
        if not os.path.exists(src):
            return ''
        return self._handle_file(src)

    def generate_string(self, string):
        """render template from string"""
        if not string:
            return ''
        return self.env.from_string(string).render()

    def add_tmp_vars(self, newvars={}):
        """add vars to the globals, make sure to call restore_vars"""
        saved_globals = self.env.globals.copy()
        if not newvars:
            return saved_globals
        self.env.globals.update(newvars)
        return saved_globals

    def restore_vars(self, saved_globals):
        """restore globals from add_tmp_vars"""
        self.env.globals = saved_globals.copy()

    def update_variables(self, variables):
        """update variables"""
        self.env.globals.update(variables)

    def _header(self, prepend=''):
        """add a comment usually in the header of a dotfile"""
        return '{}{}'.format(prepend, utils.header())

    def _handle_file(self, src):
        """generate the file content from template"""
        _, filetype = utils.run(['file', '-b', src],
                                raw=False, debug=self.debug)
        filetype = filetype.strip()
        if self.debug:
            self.log.dbg('\"{}\" filetype: {}'.format(src, filetype))
        istext = self._is_text(filetype)
        if self.debug:
            self.log.dbg('\"{}\" is text: {}'.format(src, istext))
        if not istext:
            return self._handle_bin_file(src)
        return self._handle_text_file(src)

    def _is_text(self, fileoutput):
        """return if `file -b` output is ascii text"""
        out = fileoutput.lower()
        if 'text' in out:
            return True
        if 'empty' in out:
            return True
        if 'json' in out:
            return True
        return False

    def _handle_text_file(self, src):
        """write text to file"""
        template_rel_path = os.path.relpath(src, self.base)
        try:
            template = self.env.get_template(template_rel_path)
            content = template.render()
        except UnicodeDecodeError:
            data = self._read_bad_encoded_text(src)
            content = self.generate_string(data)
        return content.encode('utf-8')

    def _handle_bin_file(self, src):
        """write binary to file"""
        # this is dirty
        if not src.startswith(self.base):
            src = os.path.join(self.base, src)
        with open(src, 'rb') as f:
            content = f.read()
        return content

    def _read_bad_encoded_text(self, path):
        """decode non utf-8 data"""
        with open(path, 'rb') as f:
            data = f.read()
        return data.decode('utf-8', 'replace')

    @staticmethod
    def is_template(path):
        """recursively check if any file is a template within path"""
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return False
        if os.path.isfile(path):
            # is file
            return Templategen._is_template(path)
        for entry in os.listdir(path):
            fpath = os.path.join(path, entry)
            if not os.path.isfile(fpath):
                # recursively explore directory
                if Templategen.is_template(fpath):
                    return True
            else:
                # check if file is a template
                if Templategen._is_template(fpath):
                    return True
        return False

    @staticmethod
    def var_is_template(string):
        """check if variable contains template(s)"""
        return VAR_START in str(string)

    @staticmethod
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
