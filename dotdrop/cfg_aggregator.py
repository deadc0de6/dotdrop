"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

handle higher level of the config file
"""

import os
import shlex
import platform
import distro


# local imports
from dotdrop.cfg_yaml import CfgYaml
from dotdrop.dotfile import Dotfile
from dotdrop.settings import Settings
from dotdrop.profile import Profile
from dotdrop.action import Action, Transform
from dotdrop.logger import Logger
from dotdrop.utils import strip_home, debug_list, debug_dict
from dotdrop.exceptions import UndefinedException, YamlException, \
    ConfigException


TILD = '~'


class CfgAggregator:
    """The config aggregator class"""

    file_prefix = 'f'
    dir_prefix = 'd'

    variable_os = 'os'
    variable_release = 'release'
    variable_distro_id = 'distro_id'
    variable_distro_like = 'distro_like'
    variable_distro_version = 'distro_version'

    def __init__(self, path, profile_key, debug=False, dry=False):
        """
        high level config parser
        @path: path to the config file
        @profile_key: profile key
        @debug: debug flag
        """
        self.path = path
        self.profile_key = profile_key
        self.debug = debug
        self.dry = dry
        self.log = Logger(debug=self.debug)
        try:
            self._load()
        except Exception as exc:
            raise YamlException(exc) from exc
        self._validate()

    ########################################################
    # public methods
    ########################################################

    def del_dotfile(self, dotfile):
        """remove this dotfile from the config"""
        return self.cfgyaml.del_dotfile(dotfile.key)

    def del_dotfile_from_profile(self, dotfile, profile):
        """remove this dotfile from this profile"""
        return self.cfgyaml.del_dotfile_from_profile(dotfile.key, profile.key)

    def new_dotfile(self, src, dst, link, chmod=None,
                    trans_install=None, trans_update=None):
        """
        import a new dotfile
        @src: path in dotpath
        @dst: path in FS
        @link: LinkType
        @chmod: file permission
        @trans_install: read transformation
        @trans_update: write transformation
        """
        dst = self.path_to_dotfile_dst(dst)
        dotfile = self.get_dotfile_by_src_dst(src, dst)
        if not dotfile:
            # add the dotfile
            dotfile = self._create_new_dotfile(src, dst, link, chmod=chmod,
                                               trans_install=trans_install,
                                               trans_update=trans_update)

        if not dotfile:
            return False
        ret = dotfile is not None

        if self.profile_key != self.cfgyaml.key_all:
            # add to profile
            key = dotfile.key
            ret = self.cfgyaml.add_dotfile_to_profile(key, self.profile_key)
            if ret:
                msg = f'new dotfile {key} to profile {self.profile_key}'
                self.log.dbg(msg)

        # save the config and reload it
        if ret:
            self._save_and_reload()
        return ret

    def update_dotfile(self, key, chmod):
        """update an existing dotfile"""
        ret = self.cfgyaml.update_dotfile(key, chmod)
        if ret:
            self._save_and_reload()
        return ret

    def path_to_dotfile_dst(self, path):
        """normalize the path to match dotfile dst"""
        path = self._norm_path(path)

        # use tild for home
        home = os.path.expanduser(TILD) + os.sep
        if path.startswith(home):
            path = path[len(home):]
            path = os.path.join(TILD, path)
        return path

    def get_dotfile_by_dst(self, dst, profile_key=None):
        """
        get a list of dotfiles by dst
        @dst: dotfile dst (on filesystem)
        """
        dotfiles = []
        dst = self._norm_path(dst)
        dfs = self.dotfiles
        if profile_key:
            dfs = self.get_dotfiles(profile_key=profile_key)
        for dotfile in dfs:
            left = self._norm_path(dotfile.dst)
            if left == dst:
                dotfiles.append(dotfile)
        return dotfiles

    def get_dotfile_by_src_dst(self, src, dst):
        """
        get a dotfile by src and dst
        @src: dotfile src (in dotpath)
        @dst: dotfile dst (on filesystem)
        """
        if not os.path.isabs(src):
            # ensures we have an absolute path
            try:
                src = self.cfgyaml.resolve_dotfile_src(src)
            except UndefinedException as exc:
                err = f'unable to resolve {src}: {exc}'
                self.log.err(err)
                return None
        dotfiles = self.get_dotfile_by_dst(dst)
        for dotfile in dotfiles:
            dsrc = self.cfgyaml.resolve_dotfile_src(dotfile.src)
            if dsrc == src:
                return dotfile
        return None

    def save(self):
        """save the config"""
        if self.dry:
            return True
        return self.cfgyaml.save()

    def dump(self):
        """dump the config dictionary"""
        return self.cfgyaml.dump()

    def get_settings(self):
        """return settings as a dict"""
        return self.settings.serialize()[Settings.key_yaml]

    def get_variables(self):
        """return variables"""
        return self.variables

    def get_profiles(self):
        """return profiles"""
        return self.profiles

    def get_profile(self, key=None):
        """return profile object"""
        pro = self.profile_key
        if key:
            pro = key

        try:
            return next(x for x in self.profiles if x.key == pro)
        except StopIteration:
            return None

    def get_profiles_by_dotfile_key(self, key):
        """return all profiles having this dotfile"""
        res = []
        for profile in self.profiles:
            keys = [dotfile.key for dotfile in profile.dotfiles]
            if key in keys:
                res.append(profile)
        return res

    def get_dotfiles(self, profile_key=None):
        """
        get all dotfiles for the current profile if None
        or the specified profile_key if defined
        or all dotfiles if profile_key is ALL
        """
        if profile_key == self.cfgyaml.key_all:
            return self.dotfiles
        dotfiles = []
        profile = self.get_profile(key=profile_key)
        if not profile:
            return dotfiles
        return profile.dotfiles

    def get_dotfile(self, key, profile_key=None):
        """
        return dotfile object by key
        @key: the dotfile key to look for
        """
        dfs = self.dotfiles
        if profile_key:
            profile = self.get_profile(key=profile_key)
            if not profile:
                return None
            dfs = profile.dotfiles
        try:
            return next(x for x in dfs
                        if x.key == key)
        except StopIteration:
            return None

    ########################################################
    # accessors for public methods
    ########################################################

    def _create_new_dotfile(self, src, dst, link, chmod=None,
                            trans_install=None, trans_update=None):
        """create a new dotfile"""
        # get a new dotfile with a unique key
        key = self._get_new_dotfile_key(dst)
        self.log.dbg(f'new dotfile key: {key}')
        # add the dotfile
        trans_install_key = trans_update_key = None
        if trans_install:
            trans_install_key = trans_install.key
        if trans_update:
            trans_update_key = trans_update.key
        if not self.cfgyaml.add_dotfile(key, src, dst, link,
                                        chmod=chmod,
                                        trans_install_key=trans_install_key,
                                        trans_update_key=trans_update_key):
            return None
        return Dotfile(key, dst, src,
                       trans_install=trans_install,
                       trans_update=trans_update)

    ########################################################
    # parsing
    ########################################################

    def _validate(self):
        """validate fields on top level view of config"""
        val = self.settings.workdir
        if not val:
            raise UndefinedException('\"workdir\" is undefined')

    def _load(self, reloading=False):
        """load lower level config"""
        self.cfgyaml = CfgYaml(self.path,
                               self.profile_key,
                               reloading=reloading,
                               debug=self.debug)

        self.log.dbg('parsing cfgyaml into cfg_aggregator')

        # settings
        self.log.dbg('parsing settings')
        self.settings = Settings.parse(None, self.cfgyaml.settings)
        self.key_prefix = self.settings.key_prefix
        self.key_separator = self.settings.key_separator

        # dotfiles
        self.log.dbg('parsing dotfiles')
        self.dotfiles = Dotfile.parse_dict(self.cfgyaml.dotfiles)
        debug_list('dotfiles', self.dotfiles, self.debug)

        # profiles
        self.log.dbg('parsing profiles')
        self.profiles = Profile.parse_dict(self.cfgyaml.profiles)
        debug_list('profiles', self.profiles, self.debug)

        # actions
        self.log.dbg('parsing actions')
        self.actions = Action.parse_dict(self.cfgyaml.actions)
        debug_list('actions', self.actions, self.debug)

        # trans_install
        self.log.dbg('parsing trans_install')
        self.trans_install = Transform.parse_dict(self.cfgyaml.trans_install)
        debug_list('trans_install', self.trans_install, self.debug)

        # trans_update
        self.log.dbg('parsing trans_update')
        self.trans_update = Transform.parse_dict(self.cfgyaml.trans_update)
        debug_list('trans_update', self.trans_update, self.debug)

        # variables
        self.log.dbg('parsing variables')
        self.variables = self.cfgyaml.variables
        debug_dict('variables', self.variables, self.debug)

        self.log.dbg('enrich variables')
        self._enrich_variables()

        self.log.dbg('patch keys...')
        # patch dotfiles in profiles
        self._patch_keys_to_objs(self.profiles,
                                 "dotfiles", self.get_dotfile)

        # patch action in dotfiles actions
        self._patch_keys_to_objs(self.dotfiles,
                                 "actions", self._get_action_w_args)
        # patch action in profiles actions
        self._patch_keys_to_objs(self.profiles,
                                 "actions", self._get_action_w_args)

        # patch actions in settings default_actions
        self._patch_keys_to_objs([self.settings],
                                 "default_actions", self._get_action_w_args)

        msg = f'default actions: {self.settings.default_actions}'
        self.log.dbg(msg)

        # patch trans_install in dotfiles
        trans_inst_args = self._get_trans_update_args(self.get_trans_install)
        self._patch_keys_to_objs(self.dotfiles,
                                 CfgYaml.key_trans_install,
                                 trans_inst_args,
                                 islist=False)
        # patch trans_update in dotfiles
        trans_update_args = self._get_trans_update_args(self.get_trans_update)
        self._patch_keys_to_objs(self.dotfiles,
                                 CfgYaml.key_trans_update,
                                 trans_update_args,
                                 islist=False)

        self.log.dbg('done parsing cfgyaml into cfg_aggregator')

    def _enrich_variables(self):
        """
        enrich available variables
        """
        if self.variable_os not in self.variables:
            # enrich with os variable
            # https://docs.python.org/3/library/platform.html#platform.system
            var_os = platform.system().lower()
            self.variables[self.variable_os] = var_os
            msg = f'enrich variables with {self.variable_os}={var_os}'
            self.log.dbg(msg)
        if self.variable_release not in self.variables:
            # enrich with release variable
            # https://docs.python.org/3/library/platform.html#platform.release
            var_release = platform.release().lower()
            self.variables[self.variable_release] = var_release
            msg = f'enrich variables with {self.variable_release}'
            msg += f'={var_release}'
            self.log.dbg(msg)
        if self.variable_distro_id not in self.variables:
            # enrich with distro variable
            # https://pypi.org/project/distro/
            # https://distro.readthedocs.io/en/latest/#distro.id
            var_distro_id = distro.id().lower()
            self.variables[self.variable_distro_id] = var_distro_id
            msg = f'enrich variables with {self.variable_distro_id}'
            msg += f'={var_distro_id}'
            self.log.dbg(msg)
        if self.variable_distro_version not in self.variables:
            # enrich with distro variable
            # https://pypi.org/project/distro/
            # https://distro.readthedocs.io/en/latest/#distro.version
            var_version = distro.version().lower()
            self.variables[self.variable_distro_version] = var_version
            msg = f'enrich variables with {self.variable_distro_version}'
            msg += f'={var_version}'
            self.log.dbg(msg)
        if self.variable_distro_like not in self.variables:
            # enrich with distro variable
            # https://pypi.org/project/distro/
            # https://distro.readthedocs.io/en/latest/#distro.like
            var_like = distro.like().lower()
            self.variables[self.variable_distro_like] = var_like
            msg = f'enrich variables with {self.variable_distro_like}'
            msg += f'={var_like}'
            self.log.dbg(msg)

    def _patch_keys_to_objs(self, containers, keys, get_by_key, islist=True):
        """
        map for each key in the attribute 'keys' in 'containers'
        the returned object from the method 'get_by_key'
        """
        if not containers:
            return
        self.log.dbg(f'patching {keys} ...')
        for container in containers:
            objects = []
            okeys = getattr(container, keys)
            if not okeys:
                continue
            if not islist:
                okeys = [okeys]
            for key in okeys:
                obj = get_by_key(key)
                if not obj:
                    err = f'{container} does not contain'
                    err += f' a {keys} entry named {key}'
                    self.log.err(err)
                    raise ConfigException(err)
                objects.append(obj)
            if not islist:
                objects = objects[0]
            setattr(container, keys, objects)

    ########################################################
    # dotfile key
    ########################################################

    def _get_new_dotfile_key(self, dst):
        """return a new unique dotfile key"""
        path = os.path.expanduser(dst)
        existing_keys = self.cfgyaml.get_all_dotfile_keys()
        if self.settings.longkey:
            return self._get_long_key(path, existing_keys)
        return self._get_short_key(path, existing_keys)

    @classmethod
    def _norm_key_elem(cls, elem):
        """normalize path element for sanity"""
        elem = elem.lstrip('.')
        elem = elem.replace(' ', '-')
        return elem.lower()

    def _get_long_key(self, path, keys):
        """
        return a unique long key representing the
        absolute path of path
        """
        dirs = self._split_path_for_key(path)
        prefix = []
        if self.key_prefix:
            prefix = [self.file_prefix]
            if os.path.isdir(path):
                prefix = [self.dir_prefix]
        key = self.key_separator.join(prefix + dirs)
        return self._uniq_key(key, keys)

    def _get_short_key(self, path, keys):
        """
        return a unique key where path
        is known not to be an already existing dotfile
        """
        dirs = self._split_path_for_key(path)
        dirs.reverse()
        prefix = []
        if self.key_prefix:
            prefix = [self.file_prefix]
            if os.path.isdir(path):
                prefix = [self.dir_prefix]
        entries = []
        for dri in dirs:
            entries.insert(0, dri)
            key = self.key_separator.join(prefix + entries)
            if key not in keys:
                return key
        return self._uniq_key(key, keys)

    def _uniq_key(self, key, keys):
        """unique dotfile key"""
        newkey = key
        cnt = 1
        while newkey in keys:
            # if unable to get a unique path
            # get a random one
            newkey = self.key_separator.join([key, str(cnt)])
            cnt += 1
        return newkey

    ########################################################
    # helpers
    ########################################################

    def _save_and_reload(self):
        if self.dry:
            return
        self.save()
        self.log.dbg('reloading config')
        olddebug = self.debug
        self.debug = False
        self._load(reloading=True)
        self.debug = olddebug

    @classmethod
    def _norm_path(cls, path):
        if not path:
            return path
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = os.path.abspath(path)
        return path

    def _split_path_for_key(self, path):
        """return a list of path elements, excluded home path"""
        path = strip_home(path)
        dirs = []
        while True:
            path, file = os.path.split(path)
            dirs.append(file)
            if not path or not file:
                break
        dirs.reverse()
        # remove empty entries
        dirs = filter(None, dirs)
        # normalize entries
        return list(map(self._norm_key_elem, dirs))

    def _get_action(self, key):
        """return action by key"""
        try:
            return next(x for x in self.actions if x.key == key)
        except StopIteration:
            return None

    def _get_action_w_args(self, key):
        """return action by key with the arguments"""
        fields = shlex.split(key)
        if len(fields) > 1:
            # we have args
            key, *args = fields
            msg = f'action with parm: {key} and {args}'
            self.log.dbg(msg)
            action = self._get_action(key).copy(args)
        else:
            action = self._get_action(key)
        return action

    def _get_trans_update_args(self, getter):
        """return transformation by key with the arguments"""
        def getit(key):
            fields = shlex.split(key)
            if len(fields) > 1:
                # we have args
                key, *args = fields
                msg = f'trans with parm: {key} and {args}'
                self.log.dbg(msg)
                trans = getter(key).copy(args)
            else:
                trans = getter(key)
            return trans
        return getit

    def get_trans_install(self, key):
        """return the trans_install with this key"""
        try:
            return next(x for x in self.trans_install if x.key == key)
        except StopIteration:
            return None

    def get_trans_update(self, key):
        """return the trans_update with this key"""
        try:
            return next(x for x in self.trans_update if x.key == key)
        except StopIteration:
            return None
