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

        # TODO
        # match dotfiles to profiles
        self._match_keys_to_obj(self.cfgyaml.profiles,
                                "dotfiles", self.get_dotfile)
        # match action to actions
        self._match_keys_to_obj(self.cfgyaml.dotfiles,
                                "actions", self.get_action,
                                copy=True)
        self._match_keys_to_obj(self.cfgyaml.profiles,
                                "actions", self.get_action,
                                copy=True)
        # match trans to trans
        # match trans_w to trans_w

    def _match_keys_to_obj(self, containers, keys, getter,
                           copy=False):
        """
        add a new attribute to containers class
        containing the object returned by getter
        for each key in keys
        """
        for c in containers:
            objects = []
            for k in getattr(c, keys):
                o = getter(k)
                if not o:
                    err = 'bad key for \"{}\": {}'.format(c.key, k)
                    raise Exception(err)
                if copy:
                    o = copy(o)
                objects.append(o)
            setattr(c, '{}_obj'.format(keys), objects)

    def new(self, src, dst, profile, link, debug=False):
        """import new dotfile"""
        args = {'src': src, 'dst': dst, 'link': link}
        return self.cfgyaml.new_dotfile(args, profile)

    def save(self):
        """save the config"""
        self.cfgyaml.save()

    def get_settings(self):
        """return a list of configs as a dict"""
        return self.cfgyaml.settings.serialize()[Settings.key_yaml]

    def get_variables(self, profile, debug=False):
        """return a list of variables as dict"""
        # TODO
        return {}

    def get_profiles(self, debug=False):
        """return a list of profiles"""
        # TODO
        return {}

    def _get_dotfiles(self, profile=None):
        """return dotfiles for this profile key"""
        if not profile:
            return self.cfgyaml.dotfiles
        p = self.get_profile(profile)
        if not p:
            return []
        return p.dotfiles_obj

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
            for action in d.actions_obj:
                action.action = t.generate_string(action.action)
        return dotfiles

    def get_dotfile(self, key):
        """get dotfile by key"""
        try:
            return next(d for d in self.cfgyaml.dotfiles if d.key == key)
        except StopIteration:
            return None

    def get_profile(self, key):
        """get profile by key"""
        try:
            return next(p for p in self.cfgyaml.profiles if p.key == key)
        except StopIteration:
            return None

    def get_action(self, key):
        """get action by key"""
        try:
            return next(p for p in self.cfgyaml.actions if p.key == key)
        except StopIteration:
            return None
