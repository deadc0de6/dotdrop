"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

yaml config file manager
"""

import yaml
import os

# local import
from dotdrop.dotfile import Dotfile
from dotdrop.logger import Logger
from dotdrop.action import Action, Transform


class Cfg:
    key_all = 'ALL'

    # settings keys
    key_settings = 'config'
    key_dotpath = 'dotpath'
    key_backup = 'backup'
    key_create = 'create'
    key_banner = 'banner'

    # actions keys
    key_actions = 'actions'
    key_actions_pre = 'pre'
    key_actions_post = 'post'

    # transformations keys
    key_trans = 'trans'

    # dotfiles keys
    key_dotfiles = 'dotfiles'
    key_dotfiles_src = 'src'
    key_dotfiles_dst = 'dst'
    key_dotfiles_link = 'link'
    key_dotfiles_actions = 'actions'
    key_dotfiles_trans = 'trans'

    # profiles keys
    key_profiles = 'profiles'
    key_profiles_dots = 'dotfiles'
    key_profiles_incl = 'include'

    # settings defaults
    default_backup = True
    default_create = True
    default_banner = True
    default_link = False

    def __init__(self, cfgpath):
        if not os.path.exists(cfgpath):
            raise ValueError('config file does not exist')
        self.cfgpath = cfgpath
        self.log = Logger()
        # link inside content
        self.settings = {}
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
        """load the yaml file"""
        with open(self.cfgpath, 'r') as f:
            self.content = yaml.load(f)
        if not self._is_valid():
            return False
        return self._parse()

    def _is_valid(self):
        """test the yaml file (self.content) is valid"""
        if self.key_profiles not in self.content:
            self.log.err('missing \"{}\" in config'.format(self.key_profiles))
            return False
        if self.key_settings not in self.content:
            self.log.err('missing \"{}\" in config'.format(self.key_settings))
            return False
        if self.key_dotfiles not in self.content:
            self.log.err('missing \"{}\" in config'.format(self.key_dotfiles))
            return False
        if self.content[self.key_profiles]:
            # make sure dotfiles are in a sub called "dotfiles"
            pro = self.content[self.key_profiles]
            tosave = False
            for k in pro.keys():
                if self.key_profiles_dots not in pro[k] and \
                        self.key_profiles_incl not in pro[k]:
                    pro[k] = {self.key_profiles_dots: pro[k]}
                    tosave = True
            if tosave:
                # save the new config file
                self._save(self.content, self.cfgpath)

        return True

    def _parse_actions(self, actions, entries):
        """parse actions specified for an element
        where actions are all known actions and
        entries are the ones defined for this dotfile"""
        res = {
            self.key_actions_pre: [],
            self.key_actions_post: [],
        }
        for entry in entries:
            action = None
            if self.key_actions_pre in actions and \
                    entry in actions[self.key_actions_pre]:
                key = self.key_actions_pre
                action = actions[self.key_actions_pre][entry]
            elif self.key_actions_post in actions and \
                    entry in actions[self.key_actions_post]:
                key = self.key_actions_post
                action = actions[self.key_actions_post][entry]
            elif entry not in actions.keys():
                self.log.warn('unknown action \"{}\"'.format(entry))
                continue
            else:
                key = self.key_actions_post
                action = actions[entry]
            res[key].append(action)
        return res

    def _parse_trans(self, trans, entries):
        """parse transformations specified for an element
        where trans are all known transformation and
        entries are the ones defined for this dotfile"""
        res = []
        for entry in entries:
            if entry not in trans.keys():
                self.log.warn('unknown trans \"{}\"'.format(entry))
                continue
            res.append(trans[entry])
        return res

    def _complete_settings(self):
        """set settings defaults if not present"""
        if self.key_backup not in self.settings:
            self.settings[self.key_backup] = self.default_backup
        if self.key_create not in self.settings:
            self.settings[self.key_create] = self.default_create
        if self.key_banner not in self.settings:
            self.settings[self.key_banner] = self.default_banner

    def _parse(self):
        """parse config file"""
        # parse all actions
        if self.key_actions in self.content:
            if self.content[self.key_actions] is not None:
                for k, v in self.content[self.key_actions].items():
                    if k in [self.key_actions_pre, self.key_actions_post]:
                        items = self.content[self.key_actions][k].items()
                        for k2, v2 in items:
                            if k not in self.actions:
                                self.actions[k] = {}
                            self.actions[k][k2] = Action(k2, v2)
                    else:
                        self.actions[k] = Action(k, v)

        # parse all transformations
        if self.key_trans in self.content:
            if self.content[self.key_trans] is not None:
                for k, v in self.content[self.key_trans].items():
                    self.trans[k] = Transform(k, v)

        # parse the profiles
        self.profiles = self.content[self.key_profiles]
        if self.profiles is None:
            self.content[self.key_profiles] = {}
            self.profiles = self.content[self.key_profiles]
        for k, v in self.profiles.items():
            if self.key_profiles_dots in v and \
                    v[self.key_profiles_dots] is None:
                v[self.key_profiles_dots] = []

        # parse the settings
        self.settings = self.content[self.key_settings]
        self._complete_settings()

        # parse the dotfiles
        if not self.content[self.key_dotfiles]:
            self.content[self.key_dotfiles] = {}
        for k, v in self.content[self.key_dotfiles].items():
            src = v[self.key_dotfiles_src]
            dst = v[self.key_dotfiles_dst]
            link = v[self.key_dotfiles_link] if self.key_dotfiles_link \
                in v else self.default_link
            entries = v[self.key_dotfiles_actions] if \
                self.key_dotfiles_actions in v else []
            actions = self._parse_actions(self.actions, entries)
            entries = v[self.key_dotfiles_trans] if \
                self.key_dotfiles_trans in v else []
            trans = self._parse_trans(self.trans, entries)
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
        self.curdotpath = self.settings[self.key_dotpath]
        self.settings[self.key_dotpath] = self.get_abs_dotpath(self.curdotpath)
        return True

    def _get_included_dotfiles(self, profile):
        """find all dotfiles for a specific include keyword"""
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
        """transform dotpath to an absolute path"""
        if not dotpath.startswith(os.sep):
            absconf = os.path.join(os.path.dirname(
                self.cfgpath), dotpath)
            return absconf
        return dotpath

    def _save(self, content, path):
        """writes the config to file"""
        ret = False
        with open(path, 'w') as f:
            ret = yaml.dump(content, f,
                            default_flow_style=False, indent=2)
        return ret

    def _get_unique_key(self, dst):
        """return a unique key for an inexistent dotfile"""
        allkeys = self.dotfiles.keys()
        idx = -1
        while True:
            key = '_'.join(dst.split(os.sep)[idx:])
            key = key.lstrip('.').lower()

            if os.path.isdir(dst):
                key = 'd_{}'.format(key)
            else:
                key = 'f_{}'.format(key)
            if key not in allkeys:
                break
            idx -= 1
        return key

    def _dotfile_exists(self, dotfile):
        """return True and the existing dotfile key
        if it already exists, False and a new unique key otherwise"""
        dsts = [(k, d.dst) for k, d in self.dotfiles.items()]
        if dotfile.dst in [x[1] for x in dsts]:
            return True, [x[0] for x in dsts if x[1] == dotfile.dst][0]
        return False, self._get_unique_key(dotfile.dst)

    def new(self, dotfile, profile, link=False):
        """import new dotfile (key will change)"""
        # keep it short
        home = os.path.expanduser('~')
        dotfile.dst = dotfile.dst.replace(home, '~')

        # adding new profile if doesn't exist
        if profile not in self.profiles:
            self.profiles[profile] = {self.key_profiles_dots: []}
            self.prodots[profile] = []

        # when dotfile already there
        exists, key = self._dotfile_exists(dotfile)
        if exists:
            dotfile = self.dotfiles[key]
            # already in it
            if dotfile in self.prodots[profile]:
                self.log.err('\"{}\" already present'.format(dotfile.key))
                return False, dotfile

            # add for this profile
            self.prodots[profile].append(dotfile)

            ent = self.content[self.key_profiles][profile]
            if self.key_all not in ent[self.key_profiles_dots]:
                ent[self.key_profiles_dots].append(dotfile.key)
            return True, dotfile

        # adding the dotfile
        dotfile.key = key
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

        # adding to global list
        self.dotfiles[dotfile.key] = dotfile
        # adding to the profile
        self.prodots[profile].append(dotfile)

        return True, dotfile

    def get_dotfiles(self, profile):
        """return a list of dotfiles for a specific profile"""
        if profile not in self.prodots:
            return []
        return sorted(self.prodots[profile],
                      key=lambda x: str(x.key))

    def get_profiles(self):
        """return all defined profiles"""
        return self.profiles.keys()

    def get_settings(self):
        """return all defined settings"""
        return self.settings.copy()

    def dump(self):
        """return a dump of the config"""
        # temporary reset dotpath
        dotpath = self.settings[self.key_dotpath]
        self.settings[self.key_dotpath] = self.curdotpath
        # reset banner
        if self.settings[self.key_banner]:
            del self.settings[self.key_banner]
        # dump
        ret = yaml.dump(self.content, default_flow_style=False, indent=2)
        # restore dotpath
        self.settings[self.key_dotpath] = dotpath
        # restore banner
        if self.key_banner not in self.settings:
            self.settings[self.key_banner] = self.default_banner
        return ret

    def save(self):
        """save the config to file"""
        # temporary reset dotpath
        dotpath = self.settings[self.key_dotpath]
        self.settings[self.key_dotpath] = self.curdotpath
        # reset banner
        if self.settings[self.key_banner]:
            del self.settings[self.key_banner]
        # save
        ret = self._save(self.content, self.cfgpath)
        # restore dotpath
        self.settings[self.key_dotpath] = dotpath
        # restore banner
        if self.key_banner not in self.settings:
            self.settings[self.key_banner] = self.default_banner
        return ret
