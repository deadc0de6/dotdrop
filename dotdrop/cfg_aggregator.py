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
from dotdrop.utils import strip_home


TILD = '~'


class CfgAggregator:

    file_prefix = 'f'
    dir_prefix = 'd'
    key_sep = '_'

    def __init__(self, path, profile=None, debug=False):
        """
        high level config parser
        @path: path to the config file
        @profile: selected profile
        @debug: debug flag
        """
        self.path = path
        self.profile = profile
        self.debug = debug
        self.log = Logger()
        self._load()

    def _load(self):
        """load lower level config"""
        self.cfgyaml = CfgYaml(self.path,
                               self.profile,
                               debug=self.debug)

        # settings
        self.settings = Settings.parse(None, self.cfgyaml.settings)
        if self.debug:
            self.log.dbg('settings: {}'.format(self.settings))

        # dotfiles
        self.dotfiles = Dotfile.parse_dict(self.cfgyaml.dotfiles)
        if self.debug:
            self.log.dbg('dotfiles: {}'.format(self.dotfiles))

        # profiles
        self.profiles = Profile.parse_dict(self.cfgyaml.profiles)
        if self.debug:
            self.log.dbg('profiles: {}'.format(self.profiles))

        # actions
        self.actions = Action.parse_dict(self.cfgyaml.actions)
        if self.debug:
            self.log.dbg('actions: {}'.format(self.actions))

        # trans_r
        self.trans_r = Transform.parse_dict(self.cfgyaml.trans_r)
        if self.debug:
            self.log.dbg('trans_r: {}'.format(self.trans_r))

        # trans_w
        self.trans_w = Transform.parse_dict(self.cfgyaml.trans_w)
        if self.debug:
            self.log.dbg('trans_w: {}'.format(self.trans_w))

        # variables
        self.variables = self.cfgyaml.get_variables()
        if self.debug:
            self.log.dbg('variables: {}'.format(self.variables))

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
        if self.debug:
            msg = 'default actions: {}'.format(self.settings.default_actions)
            self.log.dbg(msg)

        # patch trans_w/trans_r in dotfiles
        self._patch_keys_to_objs(self.dotfiles,
                                 "trans_r", self._get_trans_r, islist=False)
        self._patch_keys_to_objs(self.dotfiles,
                                 "trans_w", self._get_trans_w, islist=False)

    def _patch_keys_to_objs(self, containers, keys, get_by_key, islist=True):
        """
        map for each key in the attribute 'keys' in 'containers'
        the returned object from the method 'get_by_key'
        """
        if not containers:
            return
        if self.debug:
            self.log.dbg('patching {} ...'.format(keys))
        for c in containers:
            objects = []
            okeys = getattr(c, keys)
            if not okeys:
                continue
            if not islist:
                okeys = [okeys]
            for k in okeys:
                o = get_by_key(k)
                if not o:
                    err = 'bad {} key for \"{}\": {}'.format(keys, c, k)
                    self.log.err(err)
                    raise Exception(err)
                objects.append(o)
            if not islist:
                objects = objects[0]
            if self.debug:
                self.log.dbg('patching {}.{} with {}'.format(c, keys, objects))
            setattr(c, keys, objects)

    def del_dotfile(self, dotfile):
        """remove this dotfile from the config"""
        return self.cfgyaml.del_dotfile(dotfile.key)

    def del_dotfile_from_profile(self, dotfile, profile):
        """remove this dotfile from this profile"""
        return self.cfgyaml.del_dotfile_from_profile(dotfile.key, profile.key)

    def new(self, src, dst, link, profile_key):
        """
        import a new dotfile
        @src: path in dotpath
        @dst: path in FS
        @link: LinkType
        @profile_key: to which profile
        """
        dst = self.path_to_dotfile_dst(dst)

        dotfile = self.get_dotfile_by_dst(dst)
        if not dotfile:
            # get a new dotfile with a unique key
            key = self._get_new_dotfile_key(dst)
            if self.debug:
                self.log.dbg('new dotfile key: {}'.format(key))
            # add the dotfile
            self.cfgyaml.add_dotfile(key, src, dst, link)
            dotfile = Dotfile(key, dst, src)

        key = dotfile.key
        ret = self.cfgyaml.add_dotfile_to_profile(key, profile_key)
        if self.debug:
            self.log.dbg('new dotfile {} to profile {}'.format(key,
                                                               profile_key))

        # reload
        self.cfgyaml.save()
        if self.debug:
            self.log.dbg('RELOADING')
        self._load()
        return ret

    def _get_new_dotfile_key(self, dst):
        """return a new unique dotfile key"""
        path = os.path.expanduser(dst)
        existing_keys = [x.key for x in self.dotfiles]
        if self.settings.longkey:
            return self._get_long_key(path, existing_keys)
        return self._get_short_key(path, existing_keys)

    def _norm_key_elem(self, elem):
        """normalize path element for sanity"""
        elem = elem.lstrip('.')
        elem = elem.replace(' ', '-')
        return elem.lower()

    def _split_path_for_key(self, path):
        """return a list of path elements, excluded home path"""
        p = strip_home(path)
        dirs = []
        while True:
            p, f = os.path.split(p)
            dirs.append(f)
            if not p or not f:
                break
        dirs.reverse()
        # remove empty entries
        dirs = filter(None, dirs)
        # normalize entries
        return list(map(self._norm_key_elem, dirs))

    def _get_long_key(self, path, keys):
        """
        return a unique long key representing the
        absolute path of path
        """
        dirs = self._split_path_for_key(path)
        prefix = self.dir_prefix if os.path.isdir(path) else self.file_prefix
        key = self.key_sep.join([prefix] + dirs)
        return self._uniq_key(key, keys)

    def _get_short_key(self, path, keys):
        """
        return a unique key where path
        is known not to be an already existing dotfile
        """
        dirs = self._split_path_for_key(path)
        dirs.reverse()
        prefix = self.dir_prefix if os.path.isdir(path) else self.file_prefix
        entries = []
        for d in dirs:
            entries.insert(0, d)
            key = self.key_sep.join([prefix] + entries)
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
            newkey = self.key_sep.join([key, str(cnt)])
            cnt += 1
        return newkey

    def path_to_dotfile_dst(self, path):
        """normalize the path to match dotfile dst"""
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = os.path.abspath(path)
        home = os.path.expanduser(TILD) + os.sep

        # normalize the path
        if path.startswith(home):
            path = path[len(home):]
            path = os.path.join(TILD, path)
        return path

    def get_dotfile_by_dst(self, dst):
        """get a dotfile by dst"""
        try:
            return next(d for d in self.dotfiles if d.dst == dst)
        except StopIteration:
            return None

    def save(self):
        """save the config"""
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

    def get_profile(self, key):
        """return profile by key"""
        try:
            return next(x for x in self.profiles if x.key == key)
        except StopIteration:
            return None

    def get_profiles_by_dotfile_key(self, key):
        """return all profiles having this dotfile"""
        res = []
        for p in self.profiles:
            keys = [d.key for d in p.dotfiles]
            if key in keys:
                res.append(p)
        return res

    def get_dotfiles(self, profile=None):
        """return dotfiles dict for this profile key"""
        if not profile:
            return self.dotfiles
        try:
            pro = self.get_profile(profile)
            if not pro:
                return []
            return pro.dotfiles
        except StopIteration:
            return []

    def get_dotfile(self, key):
        """return dotfile by key"""
        try:
            return next(x for x in self.dotfiles if x.key == key)
        except StopIteration:
            return None

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
            if self.debug:
                self.log.dbg('action with parm: {} and {}'.format(key, args))
            action = self._get_action(key).copy(args)
        else:
            action = self._get_action(key)
        return action

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
