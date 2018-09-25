"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

yaml config file manager
"""

import yaml
import os
import shlex

# local import
from dotdrop.dotfile import Dotfile
from dotdrop.logger import Logger
from dotdrop.action import Action, Transform


TILD = '~'


class Cfg:
    key_all = 'ALL'

    # settings keys
    key_settings = 'config'
    key_dotpath = 'dotpath'
    key_backup = 'backup'
    key_create = 'create'
    key_banner = 'banner'
    key_long = 'longkey'
    key_keepdot = 'keepdot'
    key_deflink = 'link_by_default'
    key_workdir = 'workdir'

    # actions keys
    key_actions = 'actions'
    key_actions_pre = 'pre'
    key_actions_post = 'post'

    # transformations keys
    key_trans = 'trans'

    # template variables
    key_variables = 'variables'

    # dotfiles keys
    key_dotfiles = 'dotfiles'
    key_dotfiles_src = 'src'
    key_dotfiles_dst = 'dst'
    key_dotfiles_link = 'link'
    key_dotfiles_cmpignore = 'cmpignore'
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
    default_longkey = False
    default_keepdot = False
    default_link_by_default = False
    default_workdir = '~/.config/dotdrop'

    def __init__(self, cfgpath):
        if not os.path.exists(cfgpath):
            raise ValueError('config file does not exist: {}'.format(cfgpath))
        # make sure to have an absolute path to config file
        self.cfgpath = os.path.abspath(cfgpath)

        # init the logger
        self.log = Logger()

        # represents all entries under "config"
        # linked inside the yaml dict (self.content)
        self.lnk_settings = {}

        # represents all entries under "profiles"
        # linked inside the yaml dict (self.content)
        self.lnk_profiles = {}

        # represents all dotfiles
        # NOT linked inside the yaml dict (self.content)
        self.dotfiles = {}

        # dict of all action objects by action key
        # NOT linked inside the yaml dict (self.content)
        self.actions = {}

        # dict of all transformation objects by trans key
        # NOT linked inside the yaml dict (self.content)
        self.trans = {}

        # represents all dotfiles per profile by profile key
        # NOT linked inside the yaml dict (self.content)
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
        """test the yaml dict (self.content) is valid"""
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
            # and adapt if there are not
            profiles = self.content[self.key_profiles]
            changed = False
            for k in profiles.keys():
                if self.key_profiles_dots not in profiles[k] and \
                        self.key_profiles_incl not in profiles[k]:
                    profiles[k] = {self.key_profiles_dots: profiles[k]}
                    changed = True
            if changed:
                # save the new config file
                self._save(self.content, self.cfgpath)
        return True

    def _parse(self):
        """parse config file"""
        # parse all actions
        if self.key_actions in self.content:
            if self.content[self.key_actions] is not None:
                for k, v in self.content[self.key_actions].items():
                    # loop through all actions
                    if k in [self.key_actions_pre, self.key_actions_post]:
                        # parse pre/post actions
                        items = self.content[self.key_actions][k].items()
                        for k2, v2 in items:
                            if k not in self.actions:
                                self.actions[k] = {}
                            self.actions[k][k2] = Action(k2, v2)
                    else:
                        # parse naked actions as post actions
                        if self.key_actions_post not in self.actions:
                            self.actions[self.key_actions_post] = {}
                        self.actions[self.key_actions_post][k] = Action(k, v)

        # parse all transformations
        if self.key_trans in self.content:
            if self.content[self.key_trans] is not None:
                for k, v in self.content[self.key_trans].items():
                    self.trans[k] = Transform(k, v)

        # parse the profiles
        self.lnk_profiles = self.content[self.key_profiles]
        if self.lnk_profiles is None:
            # ensures self.lnk_profiles is a dict
            self.content[self.key_profiles] = {}
            self.lnk_profiles = self.content[self.key_profiles]
        for k, v in self.lnk_profiles.items():
            if self.key_profiles_dots in v and \
                    v[self.key_profiles_dots] is None:
                # if has the dotfiles entry but is empty
                # ensures it's an empty list
                v[self.key_profiles_dots] = []

        # parse the settings
        self.lnk_settings = self.content[self.key_settings]
        self._complete_settings()

        # parse the dotfiles
        # and construct the dict of objects per dotfile key
        if not self.content[self.key_dotfiles]:
            # ensures the dotfiles entry is a dict
            self.content[self.key_dotfiles] = {}
        for k, v in self.content[self.key_dotfiles].items():
            src = v[self.key_dotfiles_src]
            dst = v[self.key_dotfiles_dst]
            link = v[self.key_dotfiles_link] if self.key_dotfiles_link \
                in v else self.default_link
            itsactions = v[self.key_dotfiles_actions] if \
                self.key_dotfiles_actions in v else []
            actions = self._parse_actions(itsactions)
            itstrans = v[self.key_dotfiles_trans] if \
                self.key_dotfiles_trans in v else []
            trans = self._parse_trans(itstrans)
            if len(trans) > 0 and link:
                msg = 'transformations disabled for \"{}\"'.format(dst)
                msg += ' because link is True'
                self.log.warn(msg)
                trans = []
            ignores = v[self.key_dotfiles_cmpignore] if \
                self.key_dotfiles_cmpignore in v else []
            self.dotfiles[k] = Dotfile(k, dst, src,
                                       link=link, actions=actions,
                                       trans=trans, cmpignore=ignores)

        # assign dotfiles to each profile
        for k, v in self.lnk_profiles.items():
            self.prodots[k] = []
            if self.key_profiles_dots not in v:
                # ensures is a list
                v[self.key_profiles_dots] = []
            if not v[self.key_profiles_dots]:
                continue
            dots = v[self.key_profiles_dots]
            if self.key_all in dots:
                # add all if key ALL is used
                self.prodots[k] = list(self.dotfiles.values())
            else:
                # add the dotfiles
                self.prodots[k].extend([self.dotfiles[d] for d in dots])

        # handle "include" for each profile
        for k in self.lnk_profiles.keys():
            dots = self._get_included_dotfiles(k)
            self.prodots[k].extend(dots)
            # remove duplicates if any
            self.prodots[k] = list(set(self.prodots[k]))

        # make sure we have an absolute dotpath
        self.curdotpath = self.lnk_settings[self.key_dotpath]
        self.lnk_settings[self.key_dotpath] = self.abs_dotpath(self.curdotpath)
        return True

    def _get_included_dotfiles(self, profile):
        """find all dotfiles for a specific profile
        when using the include keyword"""
        included = []
        if self.key_profiles_incl not in self.lnk_profiles[profile]:
            # no include found
            return included
        if not self.lnk_profiles[profile][self.key_profiles_incl]:
            # empty include found
            return included
        for other in self.lnk_profiles[profile][self.key_profiles_incl]:
            if other not in self.prodots:
                # no such profile
                self.log.warn('unknown included profile \"{}\"'.format(other))
                continue
            included.extend(self.prodots[other])
        return included

    def _parse_actions(self, entries):
        """parse actions specified for an element
        where entries are the ones defined for this dotfile"""
        res = {
            self.key_actions_pre: [],
            self.key_actions_post: [],
        }
        for line in entries:
            fields = shlex.split(line)
            entry = fields[0]
            args = []
            if len(fields) > 1:
                args = fields[1:]
            action = None
            if self.key_actions_pre in self.actions and \
                    entry in self.actions[self.key_actions_pre]:
                key = self.key_actions_pre
                if not args:
                    action = self.actions[self.key_actions_pre][entry]
                else:
                    a = self.actions[self.key_actions_pre][entry].action
                    action = Action(key, a, *args)
            elif self.key_actions_post in self.actions and \
                    entry in self.actions[self.key_actions_post]:
                key = self.key_actions_post
                if not args:
                    action = self.actions[self.key_actions_post][entry]
                else:
                    a = self.actions[self.key_actions_post][entry].action
                    action = Action(key, a, *args)
            else:
                self.log.warn('unknown action \"{}\"'.format(entry))
                continue
            res[key].append(action)
        return res

    def _parse_trans(self, entries):
        """parse transformations specified for an element
        where entries are the ones defined for this dotfile"""
        res = []
        for entry in entries:
            if entry not in self.trans.keys():
                self.log.warn('unknown trans \"{}\"'.format(entry))
                continue
            res.append(self.trans[entry])
        return res

    def _complete_settings(self):
        """set settings defaults if not present"""
        if self.key_backup not in self.lnk_settings:
            self.lnk_settings[self.key_backup] = self.default_backup
        if self.key_create not in self.lnk_settings:
            self.lnk_settings[self.key_create] = self.default_create
        if self.key_banner not in self.lnk_settings:
            self.lnk_settings[self.key_banner] = self.default_banner
        if self.key_long not in self.lnk_settings:
            self.lnk_settings[self.key_long] = self.default_longkey
        if self.key_keepdot not in self.lnk_settings:
            self.lnk_settings[self.key_keepdot] = self.default_keepdot
        if self.key_deflink not in self.lnk_settings:
            self.lnk_settings[self.key_deflink] = self.default_link_by_default
        if self.key_workdir not in self.lnk_settings:
            self.lnk_settings[self.key_workdir] = self.default_workdir

    def abs_dotpath(self, path):
        """transform path to an absolute path based on config path"""
        if not os.path.isabs(path):
            absconf = os.path.join(os.path.dirname(
                self.cfgpath), path)
            return absconf
        return path

    def _save(self, content, path):
        """writes the config to file"""
        ret = False
        with open(path, 'w') as f:
            ret = yaml.dump(content, f,
                            default_flow_style=False, indent=2)
        return ret

    def _norm_key_elem(self, elem):
        """normalize key element for sanity"""
        elem = elem.lstrip('.')
        elem = elem.replace(' ', '-')
        return elem.lower()

    def _get_paths(self, path):
        p = self._strip_home(path)
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
        dirs = list(map(self._norm_key_elem, dirs))
        return dirs

    def _get_long_key(self, path):
        """return a long key representing the
        absolute path of path"""
        dirs = self._get_paths(path)
        # prepend with indicator
        if os.path.isdir(path):
            key = 'd_{}'.format('_'.join(dirs))
        else:
            key = 'f_{}'.format('_'.join(dirs))
        return key

    def _get_short_key(self, path, keys):
        """return a unique key where path
        is known not to be an already existing dotfile"""
        dirs = self._get_paths(path)
        dirs.reverse()
        pre = 'f'
        if os.path.isdir(path):
            pre = 'd'
        entries = []
        for d in dirs:
            entries.insert(0, d)
            key = '_'.join(entries)
            key = '{}_{}'.format(pre, key)
            if key not in keys:
                break
        return key

    def _strip_home(self, path):
        """strip home part if any"""
        path = os.path.expanduser(path)
        home = os.path.expanduser(TILD)
        if path.startswith(home):
            path = path.lstrip(home)
        return path

    def short_to_long(self):
        """transform all short keys to long keys"""
        if not self.content[self.key_dotfiles]:
            return
        match = {}
        new = {}
        # handle the entries in dotfiles
        for oldkey, v in self.content[self.key_dotfiles].items():
            path = v[self.key_dotfiles_dst]
            path = os.path.expanduser(path)
            newkey = self._get_long_key(path)
            new[newkey] = v
            match[oldkey] = newkey
        # replace with new keys
        self.content[self.key_dotfiles] = new

        # handle the entries in profiles
        for k, v in self.lnk_profiles.items():
            if self.key_profiles_dots not in v:
                continue
            if not v[self.key_profiles_dots]:
                continue
            new = []
            for oldkey in v[self.key_profiles_dots]:
                if oldkey == self.key_all:
                    continue
                newkey = match[oldkey]
                new.append(newkey)
            # replace with new keys
            v[self.key_profiles_dots] = new

    def _dotfile_exists(self, dotfile):
        """return True and the existing dotfile key
        if it already exists, False and a new unique key otherwise"""
        dsts = [(k, d.dst) for k, d in self.dotfiles.items()]
        if dotfile.dst in [x[1] for x in dsts]:
            return True, [x[0] for x in dsts if x[1] == dotfile.dst][0]
        path = os.path.expanduser(dotfile.dst)
        if self.lnk_settings[self.key_long]:
            return False, self._get_long_key(path)
        return False, self._get_short_key(path, self.dotfiles.keys())

    def new(self, dotfile, profile, link=False):
        """import new dotfile
        dotfile key will change and can be empty"""
        # keep it short
        home = os.path.expanduser('~')
        dotfile.dst = dotfile.dst.replace(home, '~', 1)

        # adding new profile if doesn't exist
        if profile not in self.lnk_profiles:
            # in the yaml
            self.lnk_profiles[profile] = {self.key_profiles_dots: []}
            # in the global list of dotfiles per profile
            self.prodots[profile] = []

        exists, key = self._dotfile_exists(dotfile)
        if exists:
            # when dotfile already there somewhere
            dotfile = self.dotfiles[key]
            if dotfile in self.prodots[profile]:
                self.log.err('\"{}\" already present'.format(dotfile.key))
                return False, dotfile

            # add for this profile
            self.prodots[profile].append(dotfile)

            # get a pointer in the yaml profiles->this_profile
            # and complete it with the new entry
            pro = self.content[self.key_profiles][profile]
            if self.key_all not in pro[self.key_profiles_dots]:
                pro[self.key_profiles_dots].append(dotfile.key)
            return True, dotfile

        # adding the new dotfile
        dotfile.key = key
        # add the entry in the yaml file
        dots = self.content[self.key_dotfiles]
        dots[dotfile.key] = {
            self.key_dotfiles_dst: dotfile.dst,
            self.key_dotfiles_src: dotfile.src,
        }
        if link:
            # set the link flag
            dots[dotfile.key][self.key_dotfiles_link] = True

        # link it to this profile in the yaml file
        pro = self.content[self.key_profiles][profile]
        if self.key_all not in pro[self.key_profiles_dots]:
            pro[self.key_profiles_dots].append(dotfile.key)

        # add it to the global list of dotfiles
        self.dotfiles[dotfile.key] = dotfile
        # add it to this profile
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
        return self.lnk_profiles.keys()

    def get_settings(self):
        """return all defined settings"""
        return self.lnk_settings.copy()

    def get_variables(self):
        if self.key_variables in self.content:
            return self.content[self.key_variables]
        return {}

    def dump(self):
        """return a dump of the config"""
        # temporary reset dotpath
        dotpath = self.lnk_settings[self.key_dotpath]
        self.lnk_settings[self.key_dotpath] = self.curdotpath
        # dump
        ret = yaml.dump(self.content, default_flow_style=False, indent=2)
        # restore dotpath
        self.lnk_settings[self.key_dotpath] = dotpath
        return ret

    def save(self):
        """save the config to file"""
        # temporary reset dotpath
        dotpath = self.lnk_settings[self.key_dotpath]
        self.lnk_settings[self.key_dotpath] = self.curdotpath
        # save
        ret = self._save(self.content, self.cfgpath)
        # restore dotpath
        self.lnk_settings[self.key_dotpath] = dotpath
        return ret
