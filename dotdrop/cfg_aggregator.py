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
from dotdrop.exceptions import UndefinedException


TILD = '~'


class CfgAggregator:

    file_prefix = 'f'
    dir_prefix = 'd'
    key_sep = '_'

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
        self.log = Logger()
        self._load()

    def _load(self):
        """load lower level config"""
        self.cfgyaml = CfgYaml(self.path,
                               self.profile_key,
                               debug=self.debug)

        # settings
        self.settings = Settings.parse(None, self.cfgyaml.settings)

        # dotfiles
        self.dotfiles = Dotfile.parse_dict(self.cfgyaml.dotfiles)
        if self.debug:
            self._debug_list('dotfiles', self.dotfiles)

        # profiles
        self.profiles = Profile.parse_dict(self.cfgyaml.profiles)
        if self.debug:
            self._debug_list('profiles', self.profiles)

        # actions
        self.actions = Action.parse_dict(self.cfgyaml.actions)
        if self.debug:
            self._debug_list('actions', self.actions)

        # trans_r
        self.trans_r = Transform.parse_dict(self.cfgyaml.trans_r)
        if self.debug:
            self._debug_list('trans_r', self.trans_r)

        # trans_w
        self.trans_w = Transform.parse_dict(self.cfgyaml.trans_w)
        if self.debug:
            self._debug_list('trans_w', self.trans_w)

        # variables
        self.variables = self.cfgyaml.variables
        if self.debug:
            self._debug_dict('variables', self.variables)

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
                    err = '{} does not contain'.format(c)
                    err += ' a {} entry named {}'.format(keys, k)
                    self.log.err(err)
                    raise Exception(err)
                objects.append(o)
            if not islist:
                objects = objects[0]
            # if self.debug:
            #     er = 'patching {}.{} with {}'
            #     self.log.dbg(er.format(c, keys, objects))
            setattr(c, keys, objects)

    def del_dotfile(self, dotfile):
        """remove this dotfile from the config"""
        return self.cfgyaml.del_dotfile(dotfile.key)

    def del_dotfile_from_profile(self, dotfile, profile):
        """remove this dotfile from this profile"""
        return self.cfgyaml.del_dotfile_from_profile(dotfile.key, profile.key)

    def _create_new_dotfile(self, src, dst, link):
        """create a new dotfile"""
        # get a new dotfile with a unique key
        key = self._get_new_dotfile_key(dst)
        if self.debug:
            self.log.dbg('new dotfile key: {}'.format(key))
        # add the dotfile
        self.cfgyaml.add_dotfile(key, src, dst, link)
        return Dotfile(key, dst, src)

    def new(self, src, dst, link):
        """
        import a new dotfile
        @src: path in dotpath
        @dst: path in FS
        @link: LinkType
        """
        dst = self.path_to_dotfile_dst(dst)
        dotfile = self.get_dotfile_by_src_dst(src, dst)
        if not dotfile:
            dotfile = self._create_new_dotfile(src, dst, link)

        key = dotfile.key
        ret = self.cfgyaml.add_dotfile_to_profile(key, self.profile_key)
        if ret and self.debug:
            msg = 'new dotfile {} to profile {}'
            self.log.dbg(msg.format(key, self.profile_key))

        self.save()
        if ret and not self.dry:
            # reload
            if self.debug:
                self.log.dbg('reloading config')
            olddebug = self.debug
            self.debug = False
            self._load()
            self.debug = olddebug
        return ret

    def _get_new_dotfile_key(self, dst):
        """return a new unique dotfile key"""
        path = os.path.expanduser(dst)
        existing_keys = self.cfgyaml.get_all_dotfile_keys()
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
        path = self._norm_path(path)

        # use tild for home
        home = os.path.expanduser(TILD) + os.sep
        if path.startswith(home):
            path = path[len(home):]
            path = os.path.join(TILD, path)
        return path

    def get_dotfile_by_dst(self, dst):
        """
        get a list of dotfiles by dst
        @dst: dotfile dst (on filesystem)
        """
        dotfiles = []
        dst = self._norm_path(dst)
        for d in self.dotfiles:
            left = self._norm_path(d.dst)
            if left == dst:
                dotfiles.append(d)
        return dotfiles

    def get_dotfile_by_src_dst(self, src, dst):
        """
        get a dotfile by src and dst
        @src: dotfile src (in dotpath)
        @dst: dotfile dst (on filesystem)
        """
        try:
            src = self.cfgyaml.resolve_dotfile_src(src)
        except UndefinedException as e:
            err = 'unable to resolve {}: {}'
            self.log.err(err.format(src, e))
            return None
        dotfiles = self.get_dotfile_by_dst(dst)
        for d in dotfiles:
            if d.src == src:
                return d
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

    def get_profile(self):
        """return profile object"""
        try:
            return next(x for x in self.profiles if x.key == self.profile_key)
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

    def get_dotfiles(self):
        """get all dotfiles for this profile"""
        dotfiles = []
        profile = self.get_profile()
        if not profile:
            return dotfiles
        return profile.dotfiles

    def get_dotfile(self, key):
        """
        return dotfile object by key
        @key: the dotfile key to look for
        """
        try:
            return next(x for x in self.dotfiles
                        if x.key == key)
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
                if self.debug:
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

    def _norm_path(self, path):
        if not path:
            return path
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = os.path.abspath(path)
        return path

    def _debug_list(self, title, elems):
        """pretty print list"""
        if not self.debug:
            return
        self.log.dbg('{}:'.format(title))
        for e in elems:
            self.log.dbg('\t- {}'.format(e))

    def _debug_dict(self, title, elems):
        """pretty print dict"""
        if not self.debug:
            return
        self.log.dbg('{}:'.format(title))
        for k, v in elems.items():
            self.log.dbg('\t- \"{}\": {}'.format(k, v))
