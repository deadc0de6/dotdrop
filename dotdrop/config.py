"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
config file manager
"""

import yaml
import os
from dotfile import Dotfile
from logger import Logger
from action import Action


class Cfg:
    key_all = 'ALL'
    key_config = 'config'
    key_dotfiles = 'dotfiles'
    key_actions = 'actions'
    key_dotpath = 'dotpath'
    key_profiles = 'profiles'
    key_profiles_dots = 'dotfiles'
    key_dotfiles_src = 'src'
    key_dotfiles_dst = 'dst'
    key_dotfiles_link = 'link'
    key_dotfiles_actions = 'actions'

    def __init__(self, cfgpath):
        if not os.path.exists(cfgpath):
            raise ValueError('config file does not exist')
        self.cfgpath = cfgpath
        self.log = Logger()
        self.configs = {}
        self.dotfiles = {}
        self.actions = {}
        self.profiles = {}
        self.prodots = {}
        if not self._load_file():
            raise ValueError('config is not valid')

    def _load_file(self):
        with open(self.cfgpath, 'r') as f:
            self.content = yaml.load(f)
        if not self._is_valid():
            return False
        return self._parse()

    def _is_valid(self):
        if self.key_profiles not in self.content:
            self.log.err('missing \"%s\" in config' % (self.key_profiles))
            return False
        if self.key_config not in self.content:
            self.log.err('missing \"%s\" in config' % (self.key_config))
            return False
        if self.key_dotfiles not in self.content:
            self.log.err('missing \"%s\" in config' % (self.key_dotfiles))
            return False
        if self.content[self.key_profiles]:
            one = list(self.content[self.key_profiles].keys())[0]
            if self.key_profiles_dots not in \
                    self.content[self.key_profiles][one]:
                self._migrate_conf()
        return True

    def _migrate_conf(self):
        """ make sure dotfiles are in a sub
        "dotfiles" entry in profiles (#12) """
        new = {}
        for k, v in self.content[self.key_profiles].items():
            new[k] = {self.key_profiles_dots: v}
        self.content[self.key_profiles] = new
        self._save(self.content, self.cfgpath)

    def _parse_actions(self, actions, entries):
        """ parse actions specified for an element """
        res = []
        for entry in entries:
            if entry in actions.keys():
                res.append(actions[entry])
            else:
                self.log.err('unknown action \"%s\"' % (entry))
                return False, []
        return True, res

    def _parse(self):
        """ parse config file """
        # parse all actions
        if self.key_actions in self.content:
            if self.content[self.key_actions] is not None:
                for k, v in self.content[self.key_actions].items():
                    self.actions[k] = Action(k, v)
        # parse the profiles
        self.profiles = self.content[self.key_profiles]
        if self.profiles is None:
            self.profiles = {}
            self.content[self.key_profiles] = {}
        # parse the configs
        self.configs = self.content[self.key_config]
        # parse the dotfiles
        if self.content[self.key_dotfiles] is not None:
            for k, v in self.content[self.key_dotfiles].items():
                src = v[self.key_dotfiles_src]
                dst = v[self.key_dotfiles_dst]
                link = v[self.key_dotfiles_link] if self.key_dotfiles_link \
                    in v else False
                entries = v[self.key_dotfiles_actions] if \
                    self.key_dotfiles_actions in v else []
                res, actions = self._parse_actions(self.actions, entries)
                if not res:
                    return False
                self.dotfiles[k] = Dotfile(k, dst, src,
                                           link=link, actions=actions)
        # attribute dotfiles to each profile
        for k, v in self.profiles.items():
            self.prodots[k] = []
            dots = None
            if self.key_profiles_dots in v:
                dots = v[self.key_profiles_dots]
            if dots is None:
                continue
            if len(dots) == 1 and dots == [self.key_all]:
                self.prodots[k] = self.dotfiles.values()
            else:
                self.prodots[k].extend([self.dotfiles[d] for d in dots])
        # make sure we have an absolute dotpath
        self.curdotpath = self.configs[self.key_dotpath]
        self.configs[self.key_dotpath] = self._get_abs_dotpath(self.curdotpath)
        return True

    def _get_abs_dotpath(self, dotpath):
        """ transform dotpath to an absolute path """
        if not dotpath.startswith(os.sep):
            absconf = os.path.join(os.path.dirname(
                self.cfgpath), dotpath)
            return absconf
        return dotpath

    def new(self, dotfile, profile, link=False):
        """ import new dotfile """
        dots = self.content[self.key_dotfiles]
        if dots is None:
            self.content[self.key_dotfiles] = {}
            dots = self.content[self.key_dotfiles]
        if self.content[self.key_dotfiles] and dotfile.key in dots:
            self.log.err('\"%s\" entry already exists in dotfiles' %
                         (dotfile.key))
            return False
        home = os.path.expanduser('~')
        dotfile.dst = dotfile.dst.replace(home, '~')
        dots[dotfile.key] = {
            self.key_dotfiles_dst: dotfile.dst,
            self.key_dotfiles_src: dotfile.src
        }

        if link:
            dots[dotfile.key][self.key_dotfiles_link] = True

        profiles = self.profiles
        if profile in profiles and \
                profiles[profile][self.key_profiles_dots] != [self.key_all]:
            # existing profile and not ALL
            pro = self.content[self.key_profiles][profile]
            if not pro[self.key_profiles_dots]:
                pro[self.key_profiles_dots] = []
            pro[self.key_profiles_dots].append(dotfile.key)
        elif profile not in profiles:
            # new profile
            if profile not in self.content[self.key_profiles]:
                self.content[self.key_profiles][profile] = {}
            pro = self.content[self.key_profiles][profile]
            pro[self.key_profiles_dots] = [dotfile.key]
        # assign profiles to the content
        self.profiles = self.content[self.key_profiles]

    def get_dotfiles(self, profile):
        """ returns a list of dotfiles for a specific profile """
        if profile not in self.prodots:
            return []
        return sorted(self.prodots[profile], key=lambda x: x.key, reverse=True)

    def get_profiles(self):
        """ returns all defined profiles """
        return self.profiles.keys()

    def get_configs(self):
        """ returns all defined configs """
        return self.configs.copy()

    def dump(self):
        """ dump config file """
        # temporary reset dotpath
        tmp = self.configs[self.key_dotpath]
        self.configs[self.key_dotpath] = self.curdotpath
        ret = yaml.dump(self.content, default_flow_style=False, indent=2)
        # restore dotpath
        self.configs[self.key_dotpath] = tmp
        return ret

    def save(self):
        """ save config file to path """
        # temporary reset dotpath
        tmp = self.configs[self.key_dotpath]
        self.configs[self.key_dotpath] = self.curdotpath
        ret = self._save(self.content, self.cfgpath)
        # restore dotpath
        self.configs[self.key_dotpath] = tmp
        return ret

    def _save(self, content, path):
        ret = False
        with open(path, 'w') as f:
            ret = yaml.dump(content, f,
                            default_flow_style=False, indent=2)
        return ret
