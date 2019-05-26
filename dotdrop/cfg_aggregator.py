"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

config manager
"""

from dotdrop.cfg_yaml import CfgYaml
from dotdrop.templategen import Templategen
from dotdrop.settings import Settings


class CfgAggregator:

    def __init__(self, path, profile=None, debug=False):
        """
        Config aggregator
        @path: config file path
        """
        self.path = path
        self.profile = profile
        self.debug = debug

        # load the config file
        self._load()

    def _load(self):
        """load lower level config"""
        self.cfgyaml = CfgYaml(path=self.path,
                               debug=self.debug)

        # patch dotfiles in profiles
        self._patch_keys_to_objs(self.cfgyaml.profiles,
                                 "dotfiles", self.get_dotfile)
        # patch action in actions
        self._patch_keys_to_objs(self.cfgyaml.dotfiles,
                                 "actions", self.get_action)
        self._patch_keys_to_objs(self.cfgyaml.profiles,
                                 "actions", self.get_action)
        # patch default actions in settings
        self._patch_keys_to_objs([self.cfgyaml.settings],
                                 "default_actions", self.get_action)
        # patch trans_w/trans_r in dotfiles
        self._patch_keys_to_objs(self.cfgyaml.dotfiles,
                                 "trans_r", self.get_trans_r)
        self._patch_keys_to_objs(self.cfgyaml.dotfiles,
                                 "trans_w", self.get_trans_w)

    def _patch_keys_to_objs(self, containers, keys, get_by_key):
        """
        patch each object in containers containing
        a list of keys in the attribute "keys" with
        the returned object of the function "get_by_key"
        """
        if not containers:
            return
        for c in containers:
            objects = []
            okeys = getattr(c, keys)
            if not okeys:
                continue
            for k in okeys:
                o = get_by_key(k)
                if not o:
                    err = 'bad key for \"{}\": {}'.format(c.key, k)
                    raise Exception(err)
                objects.append(o)
            setattr(c, keys, objects)

    def new(self, src, dst, profile, link, debug=False):
        """import new dotfile"""
        args = {'src': src, 'dst': dst, 'link': link}
        return self.cfgyaml.new_dotfile(args, profile)

    def save(self):
        """save the config"""
        return self.cfgyaml.save()

    def dump(self):
        """dump the config dictionary"""
        return self.cfgyaml.dump()

    def get_settings(self):
        """return a list of configs as a dict"""
        return self.cfgyaml.settings.serialize()[Settings.key_yaml]

    def get_variables(self, profile, debug=False):
        """return a list of variables as dict"""
        return self.cfgyaml.variables

    def get_profiles(self, debug=False):
        """return a list of profiles"""
        return self.cfgyaml.profiles

    def _get_dotfiles(self, profile=None):
        """return dotfiles for this profile key"""
        if not profile:
            return self.cfgyaml.dotfiles
        p = self.get_profile(profile)
        if not p:
            return []
        return p.dotfiles

    def get_dotfiles(self, profile=None, variables=[], debug=False):
        """resolve dotfiles src/dst/actions templating for this profile key"""
        t = Templategen(variables=variables)
        dotfiles = self._get_dotfiles(profile)
        tvars = t.add_tmp_vars()
        for d in dotfiles:
            # add dotfile variables
            t.restore_vars(tvars)
            newvar = d.get_vars()
            t.add_tmp_vars(newvars=newvar)
            # src and dst path
            d.src = t.generate_string(d.src)
            d.dst = t.generate_string(d.dst)
            # actions
            for action in d.actions:
                action.action = t.generate_string(action.action)
        return dotfiles

    def get_dotfile(self, key):
        """get dotfile by key"""
        try:
            return next(x for x in self.cfgyaml.dotfiles if x.key == key)
        except StopIteration:
            return None

    def get_profile(self, key):
        """get profile by key"""
        try:
            return next(x for x in self.cfgyaml.profiles if x.key == key)
        except StopIteration:
            return None

    def get_action(self, key):
        """get action by key"""
        try:
            return next(x for x in self.cfgyaml.actions if x.key == key)
        except StopIteration:
            return None

    def get_trans_r(self, key):
        """get trans_r by key"""
        try:
            return next(x for x in self.cfgyaml.trans_r if x.key == key)
        except StopIteration:
            return None

    def get_trans_w(self, key):
        """get trans_w by key"""
        try:
            return next(x for x in self.cfgyaml.trans_w if x.key == key)
        except StopIteration:
            return None
