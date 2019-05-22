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
        self.cfgyaml = CfgYaml(yaml_dict=None, file_name=self.path,
                               debug=self.debug)

        # match dotfiles to profiles
        # TODO

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

    def _get_dotfiles(self, profile):
        """return all dotfiles for this profile"""
        # TODO
        # dfs = self.cfgyaml.dotfiles
        return []

    def get_dotfiles(self, profile, variables, debug=False):
        """resolve dotfiles src/dst/actions templating for this profile"""
        # TODO
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
            # pre actions
            if self.key_actions_pre in d.actions:
                for action in d.actions[self.key_actions_pre]:
                    action.action = t.generate_string(action.action)
            # post actions
            if self.key_actions_post in d.actions:
                for action in d.actions[self.key_actions_post]:
                    action.action = t.generate_string(action.action)
        return dotfiles
