"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

handle higher level of the config file
"""

import os
import shlex


# local imports
from dotdrop.cfg_yaml import CfgYaml
from dotdrop.dotfile import Dotfile
from dotdrop.settings import Settings
from dotdrop.profile import Profile
from dotdrop.action import Action, Transform
from dotdrop.logger import Logger
from dotdrop.utils import strip_home, debug_list, debug_dict
from dotdrop.exceptions import UndefinedException


TILD = '~'


class CfgAggregator:
    """The config aggregator class"""

    file_prefix = 'f'
    dir_prefix = 'd'

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
        self._load()
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

    def new_dotfile(self, src, dst, link, chmod=None):
        """
        import a new dotfile
        @src: path in dotpath
        @dst: path in FS
        @link: LinkType
        @chmod: file permission
        """
        dst = self.path_to_dotfile_dst(dst)
        dotfile = self.get_dotfile_by_src_dst(src, dst)
        if not dotfile:
            dotfile = self._create_new_dotfile(src, dst, link, chmod=chmod)

        if not dotfile:
            return False

        key = dotfile.key
        ret = self.cfgyaml.add_dotfile_to_profile(key, self.profile_key)
        if ret:
            msg = 'new dotfile {} to profile {}'
            self.log.dbg(msg.format(key, self.profile_key))

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
        try:
            src = self.cfgyaml.resolve_dotfile_src(src)
        except UndefinedException as exc:
            err = 'unable to resolve {}: {}'
            self.log.err(err.format(src, exc))
            return None
        dotfiles = self.get_dotfile_by_dst(dst)
        for dotfile in dotfiles:
            if dotfile.src == src:
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
        """get all dotfiles for this profile or specified profile key"""
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

    def _create_new_dotfile(self, src, dst, link, chmod=None):
        """create a new dotfile"""
        # get a new dotfile with a unique key
        key = self._get_new_dotfile_key(dst)
        self.log.dbg('new dotfile key: {}'.format(key))
        # add the dotfile
        if not self.cfgyaml.add_dotfile(key, src, dst, link, chmod=chmod):
            return None
        return Dotfile(key, dst, src)

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

        # settings
        self.settings = Settings.parse(None, self.cfgyaml.settings)
        self.key_prefix = self.settings.key_prefix
        self.key_separator = self.settings.key_separator

        # dotfiles
        self.dotfiles = Dotfile.parse_dict(self.cfgyaml.dotfiles)
        debug_list('dotfiles', self.dotfiles, self.debug)

        # profiles
        self.profiles = Profile.parse_dict(self.cfgyaml.profiles)
        debug_list('profiles', self.profiles, self.debug)

        # actions
        self.actions = Action.parse_dict(self.cfgyaml.actions)
        debug_list('actions', self.actions, self.debug)

        # trans_r
        self.trans_r = Transform.parse_dict(self.cfgyaml.trans_r)
        debug_list('trans_r', self.trans_r, self.debug)

        # trans_w
        self.trans_w = Transform.parse_dict(self.cfgyaml.trans_w)
        debug_list('trans_w', self.trans_w, self.debug)

        # variables
        self.variables = self.cfgyaml.variables
        debug_dict('variables', self.variables, self.debug)

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

        msg = 'default actions: {}'.format(self.settings.default_actions)
        self.log.dbg(msg)

        # patch trans_w/trans_r in dotfiles
        self._patch_keys_to_objs(self.dotfiles,
                                 "trans_r",
                                 self._get_trans_w_args(self._get_trans_r),
                                 islist=False)
        self._patch_keys_to_objs(self.dotfiles,
                                 "trans_w",
                                 self._get_trans_w_args(self._get_trans_w),
                                 islist=False)

    def _patch_keys_to_objs(self, containers, keys, get_by_key, islist=True):
        """
        map for each key in the attribute 'keys' in 'containers'
        the returned object from the method 'get_by_key'
        """
        if not containers:
            return
        self.log.dbg('patching {} ...'.format(keys))
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
                    err = '{} does not contain'.format(container)
                    err += ' a {} entry named {}'.format(keys, key)
                    self.log.err(err)
                    raise Exception(err)
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
            msg = 'action with parm: {} and {}'
            self.log.dbg(msg.format(key, args))
            action = self._get_action(key).copy(args)
        else:
            action = self._get_action(key)
        return action

    def _get_trans_w_args(self, getter):
        """return transformation by key with the arguments"""
        def getit(key):
            fields = shlex.split(key)
            if len(fields) > 1:
                # we have args
                key, *args = fields
                msg = 'trans with parm: {} and {}'
                self.log.dbg(msg.format(key, args))
                trans = getter(key).copy(args)
            else:
                trans = getter(key)
            return trans
        return getit

    def _get_trans_r(self, key):
        """return the trans_r with this key"""
        try:
            return next(x for x in self.trans_r if x.key == key)
        except StopIteration:
            return None

    def _get_trans_w(self, key):
        """return the trans_w with this key"""
        try:
            return next(x for x in self.trans_w if x.key == key)
        except StopIteration:
            return None
