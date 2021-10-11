"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

jinja2 template generator
"""

import os
import io
import re
import mmap
from jinja2 import Environment, FileSystemLoader, \
    ChoiceLoader, FunctionLoader, TemplateNotFound, \
    StrictUndefined
from jinja2.exceptions import UndefinedError


# local imports
from dotdrop import utils
from dotdrop import jhelpers
from dotdrop.logger import Logger
from dotdrop.exceptions import UndefinedException

BLOCK_START = '{%@@'
BLOCK_END = '@@%}'
VAR_START = '{{@@'
VAR_END = '@@}}'
COMMENT_START = '{#@@'
COMMENT_END = '@@#}'
LOG = Logger()


class Templategen:
    """dotfile templater"""

    def __init__(self, base='.', variables=None,
                 func_file=None, filter_file=None, debug=False):
        """constructor
        @base: directory path where to search for templates
        @variables: dictionary of variables for templates
        @func_file: file path to load functions from
        @filter_file: file path to load filters from
        @debug: enable debug
        """
        self.base = base.rstrip(os.sep)
        self.debug = debug
        self.log = Logger(debug=self.debug)
        self.variables = {}
        loader1 = FileSystemLoader(self.base)
        loader2 = FunctionLoader(self._template_loader)
        loader = ChoiceLoader([loader1, loader2])
        self.env = Environment(loader=loader,
                               trim_blocks=True, lstrip_blocks=True,
                               keep_trailing_newline=True,
                               block_start_string=BLOCK_START,
                               block_end_string=BLOCK_END,
                               variable_start_string=VAR_START,
                               variable_end_string=VAR_END,
                               comment_start_string=COMMENT_START,
                               comment_end_string=COMMENT_END,
                               undefined=StrictUndefined)

        # adding variables
        self.variables['env'] = os.environ
        if variables:
            self.variables.update(variables)

        # adding header method
        self.env.globals['header'] = self._header
        # adding helper methods
        self.log.dbg('load global functions:')
        self._load_funcs_to_dic(jhelpers, self.env.globals)
        if func_file:
            for ffile in func_file:
                self.log.dbg('load custom functions from {}'.format(ffile))
                self._load_path_to_dic(ffile, self.env.globals)
        if filter_file:
            for ffile in filter_file:
                self.log.dbg('load custom filters from {}'.format(ffile))
                self._load_path_to_dic(ffile, self.env.filters)
        if self.debug:
            self._debug_dict('template additional variables', variables)

    def generate(self, src):
        """
        render template from path
        may raise a UndefinedException
        in case a variable is undefined
        """
        if not os.path.exists(src):
            return ''
        try:
            return self._handle_file(src)
        except UndefinedError as exc:
            err = 'undefined variable: {}'.format(exc.message)
            raise UndefinedException(err) from exc

    def generate_string(self, string):
        """
        render template from string
        may raise a UndefinedException
        in case a variable is undefined
        """
        if not string:
            return ''
        try:
            return self.env.from_string(string).render(self.variables)
        except UndefinedError as exc:
            err = 'undefined variable: {}'.format(exc.message)
            raise UndefinedException(err) from exc

    def add_tmp_vars(self, newvars=None):
        """add vars to the globals, make sure to call restore_vars"""
        saved_variables = self.variables.copy()
        if not newvars:
            return saved_variables
        self.variables.update(newvars)
        return saved_variables

    def restore_vars(self, saved_globals):
        """restore globals from add_tmp_vars"""
        self.variables = saved_globals.copy()

    def update_variables(self, variables):
        """update variables"""
        self.variables.update(variables)

    def _load_path_to_dic(self, path, dic):
        mod = utils.get_module_from_path(path)
        if not mod:
            self.log.warn('cannot load module \"{}\"'.format(path))
            return
        self._load_funcs_to_dic(mod, dic)

    def _load_funcs_to_dic(self, mod, dic):
        """dynamically load functions from module to dic"""
        if not mod or not dic:
            return
        funcs = utils.get_module_functions(mod)
        for name, func in funcs:
            self.log.dbg('load function \"{}\"'.format(name))
            dic[name] = func

    @classmethod
    def _header(cls, prepend=''):
        """add a comment usually in the header of a dotfile"""
        return '{}{}'.format(prepend, utils.header())

    def _handle_file(self, src):
        """generate the file content from template"""
        try:
            # pylint: disable=C0415
            import magic
            filetype = magic.from_file(src, mime=True)
            self.log.dbg('using \"magic\" for filetype identification')
        except ImportError:
            # fallback
            _, filetype = utils.run(['file', '-b', '--mime-type', src],
                                    debug=self.debug)
            self.log.dbg('using \"file\" for filetype identification')
            filetype = filetype.strip()
        istext = self._is_text(filetype)
        self.log.dbg('filetype \"{}\": {}'.format(src, filetype))
        self.log.dbg('is text \"{}\": {}'.format(src, istext))
        if not istext:
            return self._handle_bin_file(src)
        return self._handle_text_file(src)

    @classmethod
    def _is_text(cls, fileoutput):
        """return if `file -b` output is ascii text"""
        out = fileoutput.lower()
        if out.startswith('text'):
            return True
        if 'empty' in out:
            return True
        if 'json' in out:
            return True
        return False

    def _template_loader(self, relpath):
        """manually load template when outside of base"""
        path = os.path.join(self.base, relpath)
        path = os.path.normpath(path)
        if not os.path.exists(path):
            raise TemplateNotFound(path)
        with open(path, 'r', encoding='utf8') as file:
            content = file.read()
        return content

    def _handle_text_file(self, src):
        """write text to file"""
        template_rel_path = os.path.relpath(src, self.base)
        try:
            template = self.env.get_template(template_rel_path)
            content = template.render(self.variables)
        except UnicodeDecodeError:
            data = self._read_bad_encoded_text(src)
            content = self.generate_string(data)
        return content.encode('utf-8')

    def _handle_bin_file(self, src):
        """write binary to file"""
        # this is dirty
        if not src.startswith(self.base):
            src = os.path.join(self.base, src)
        with open(src, 'rb') as file:
            content = file.read()
        return content

    @classmethod
    def _read_bad_encoded_text(cls, path):
        """decode non utf-8 data"""
        with open(path, 'rb') as file:
            data = file.read()
        return data.decode('utf-8', 'replace')

    @staticmethod
    def is_template(path, ignore=None, debug=False):
        """recursively check if any file is a template within path"""
        if debug:
            LOG.dbg('is template: {}'.format(path), force=True)
        path = os.path.expanduser(path)

        if not os.path.exists(path):
            # does not exist
            return False

        if utils.must_ignore([path], ignore, debug=debug):
            # must be ignored
            return False

        if os.path.isfile(path):
            # is file
            return Templategen._is_template(path, ignore=ignore, debug=debug)

        # is a directory
        for entry in os.listdir(path):
            fpath = os.path.join(path, entry)
            if not os.path.isfile(fpath):
                # recursively explore directory
                if Templategen.is_template(fpath, ignore=ignore, debug=debug):
                    return True
            else:
                # check if file is a template
                if Templategen._is_template(fpath, ignore=ignore, debug=debug):
                    return True
        return False

    @staticmethod
    def var_is_template(string):
        """check if variable contains template(s)"""
        return VAR_START in str(string)

    @staticmethod
    def _is_template(path, ignore, debug=False):
        """test if file pointed by path is a template"""
        if utils.must_ignore([path], ignore, debug=debug):
            return False
        if not os.path.isfile(path):
            return False
        if os.stat(path).st_size == 0:
            return False
        markers = [BLOCK_START, VAR_START, COMMENT_START]
        patterns = [re.compile(marker.encode()) for marker in markers]
        try:
            with io.open(path, "r", encoding="utf-8") as file:
                mapf = mmap.mmap(file.fileno(), 0,
                                 access=mmap.ACCESS_READ)
                for pattern in patterns:
                    if pattern.search(mapf):
                        return True
        except UnicodeDecodeError:
            # is binary so surely no template
            return False
        return False

    def _debug_dict(self, title, elems):
        """pretty print dict"""
        if not self.debug:
            return
        self.log.dbg('{}:'.format(title))
        if not elems:
            return
        for k, val in elems.items():
            self.log.dbg('  - \"{}\": {}'.format(k, val))
