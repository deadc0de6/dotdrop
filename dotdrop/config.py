"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6
config file manager
"""

import yaml
import os

# local import
from dotdrop.dotfile import Dotfile
from dotdrop.logger import Logger
from dotdrop.action import Action


class Cfg:
    key_all = 'ALL'
    key_config = 'config'
    key_dotfiles = 'dotfiles'
    key_actions = 'actions'
    key_trans = 'trans'
    key_dotpath = 'dotpath'
    key_profiles = 'profiles'
    key_profiles_dots = 'dotfiles'
    key_profiles_incl = 'include'
    key_dotfiles_src = 'src'
    key_dotfiles_dst = 'dst'
    key_dotfiles_link = 'link'
    key_dotfiles_actions = 'actions'
    key_dotfiles_trans = 'trans'

    def __init__(self, cfgpath):
        if not os.path.exists(cfgpath):
            raise ValueError('config file does not exist')
        self.cfgpath = cfgpath
        self.log = Logger()
        # link inside content
        self.configs = {}
        # link inside content
        self.profiles = {}
        # not linked to content
        self.dotfiles = {}
        # not linked to content
        self.actions = {}
        # not linked to content
        self.trans = {}
        # not linked to content
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
            self.log.err('missing \"{}\" in config'.format(self.key_profiles))
            return False
        if self.key_config not in self.content:
            self.log.err('missing \"{}\" in config'.format(self.key_config))
            return False
        if self.key_dotfiles not in self.content:
            self.log.err('missing \"{}\" in config'.format(self.key_dotfiles))
            return False
        if self.content[self.key_profiles]:
            # make sure dotfiles are in a sub called "dotfiles"
            pro = self.content[self.key_profiles]
            tosave = False
            for k in pro.keys():
                if self.key_profiles_dots not in pro[k]:
                    pro[k] = {self.key_profiles_dots: pro[k]}
                    tosave = True
            if tosave:
                # save the new config file
                self._save(self.content, self.cfgpath)

        return True

    def _parse_actions(self, actions, entries):
        """ parse actions specified for an element """
        res = []
        for entry in entries:
            if entry not in actions.keys():
                self.log.warn('unknown action \"{}\"'.format(entry))
                continue
            res.append(actions[entry])
        return res

    def _parse(self):
        """ parse config file """
        # parse all actions
        if self.key_actions in self.content:
            if self.content[self.key_actions] is not None:
                for k, v in self.content[self.key_actions].items():
                    self.actions[k] = Action(k, v)

        # parse all transformations
        if self.key_trans in self.content:
            if self.content[self.key_trans] is not None:
                for k, v in self.content[self.key_trans].items():
                    self.trans[k] = Action(k, v)

        # parse the profiles
        self.profiles = self.content[self.key_profiles]
        if self.profiles is None:
            self.content[self.key_profiles] = {}
            self.profiles = self.content[self.key_profiles]
        for k, v in self.profiles.items():
            if v[self.key_profiles_dots] is None:
                v[self.key_profiles_dots] = []

        # parse the configs
        self.configs = self.content[self.key_config]

        # parse the dotfiles
        if not self.content[self.key_dotfiles]:
            self.content[self.key_dotfiles] = {}
        for k, v in self.content[self.key_dotfiles].items():
            src = v[self.key_dotfiles_src]
            dst = v[self.key_dotfiles_dst]
            link = v[self.key_dotfiles_link] if self.key_dotfiles_link \
                in v else False
            entries = v[self.key_dotfiles_actions] if \
                self.key_dotfiles_actions in v else []
            actions = self._parse_actions(self.actions, entries)
            entries = v[self.key_dotfiles_trans] if \
                self.key_dotfiles_trans in v else []
            trans = self._parse_actions(self.trans, entries)
            if len(trans) > 0 and link:
                msg = 'transformations disabled for \"{}\"'.format(dst)
                msg += ' because link is True'
                self.log.warn(msg)
                trans = []
            self.dotfiles[k] = Dotfile(k, dst, src, link=link,
                                       actions=actions,
                                       trans=trans)

        # assign dotfiles to each profile
        for k, v in self.profiles.items():
            self.prodots[k] = []
            if self.key_profiles_dots not in v:
                v[self.key_profiles_dots] = []
            if not v[self.key_profiles_dots]:
                continue
            dots = v[self.key_profiles_dots]
            if self.key_all in dots:
                self.prodots[k] = list(self.dotfiles.values())
            else:
                self.prodots[k].extend([self.dotfiles[d] for d in dots])

        # handle "include" for each profile
        for k in self.profiles.keys():
            dots = self._get_included_dotfiles(k)
            self.prodots[k].extend(dots)
            # no duplicates
            self.prodots[k] = list(set(self.prodots[k]))

        # make sure we have an absolute dotpath
        self.curdotpath = self.configs[self.key_dotpath]
        self.configs[self.key_dotpath] = self.get_abs_dotpath(self.curdotpath)
        return True

    def _get_included_dotfiles(self, profile):
        included = []
        if self.key_profiles_incl not in self.profiles[profile]:
            return included
        if not self.profiles[profile][self.key_profiles_incl]:
            return included
        for other in self.profiles[profile][self.key_profiles_incl]:
            if other not in self.prodots:
                self.log.warn('unknown included profile \"{}\"'.format(other))
                continue
            included.extend(self.prodots[other])
        return included

    def get_abs_dotpath(self, dotpath):
        """ transform dotpath to an absolute path """
        if not dotpath.startswith(os.sep):
            absconf = os.path.join(os.path.dirname(
                self.cfgpath), dotpath)
            return absconf
        return dotpath

    def _save(self, content, path):
        ret = False
        with open(path, 'w') as f:
            ret = yaml.dump(content, f,
                            default_flow_style=False, indent=2)
        return ret

    def new(self, dotfile, profile, link=False):
        """ import new dotfile """
        # keep it short
        home = os.path.expanduser('~')
        dotfile.dst = dotfile.dst.replace(home, '~')

        # ensure content is valid
        if profile not in self.profiles:
            self.profiles[profile] = {self.key_profiles_dots: []}

        # when dotfile already there
        if dotfile.key in self.dotfiles.keys():
            # already in it
            if profile in self.prodots and dotfile in self.prodots[profile]:
                self.log.err('\"{}\" already present'.format(dotfile.key))
                return False

            # add for this profile
            if profile not in self.prodots:
                self.prodots[profile] = []
            self.prodots[profile].append(dotfile)

            ent = self.content[self.key_profiles][profile]
            if self.key_all not in ent[self.key_profiles_dots]:
                ent[self.key_profiles_dots].append(dotfile.key)
            return True

        # adding the dotfile
        dots = self.content[self.key_dotfiles]
        dots[dotfile.key] = {
            self.key_dotfiles_dst: dotfile.dst,
            self.key_dotfiles_src: dotfile.src,
        }
        if link:
            # avoid putting it everywhere
            dots[dotfile.key][self.key_dotfiles_link] = True

        # link it to this profile
        pro = self.content[self.key_profiles][profile]
        if self.key_all not in pro[self.key_profiles_dots]:
            pro[self.key_profiles_dots].append(dotfile.key)

        return True

    def get_dotfiles(self, profile):
        """ returns a list of dotfiles for a specific profile """
        if profile not in self.prodots:
            return []
        return sorted(self.prodots[profile],
                      key=lambda x: str(x.key))

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
