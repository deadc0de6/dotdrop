"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

yaml config file manager
"""

import os
import yaml
from operator import attrgetter

# local import
from dotdrop.utils import strip_home, clear_none
from dotdrop.dotfile import Dotfile
from dotdrop.logger import Logger
from dotdrop.profile import Profile
from dotdrop.settings import Settings
from dotdrop.action import Action, Trans_r, Trans_w
from dotdrop.variable import Variable, DynVariable


class CfgYaml:

    dotfile_key_file_prefix = 'f'
    dotfile_key_directory_prefix = 'd'

    default_settings = Settings(None)
    log = Logger()

    def __init__(self, path, debug=False):
        """constructor
        @path: path to the config file
        @debug: enable debug
        """

        self._dirty = False
        self.debug = debug

        self.path = os.path.abspath(path)
        self.yaml_dict = self._load_yaml(self.path)
        self.yaml_dict = self._sanitize_yaml(self.yaml_dict)

        self.settings = Settings.parse(self.yaml_dict, self.path)
        self.dotfiles = Dotfile.parse_dict(self.yaml_dict)
        self.profiles = Profile.parse_dict(self.yaml_dict)
        # TODO
        self.actions = Action.parse_dict(self.yaml_dict, mandatory=False)
        self.trans_r = Trans_r.parse_dict(self.yaml_dict, mandatory=False)
        self.trans_w = Trans_w.parse_dict(self.yaml_dict, mandatory=False)
        self.variables = Variable.parse_dict(self.yaml_dict, mandatory=False)
        self.dvariables = DynVariable.parse_dict(self.yaml_dict,
                                                 mandatory=False)

        self.yaml_dict.update(self.settings.serialize())

    def _load_yaml(self, path):
        """load a yaml file to a dict"""
        content = {}
        if not os.path.exists(path):
            return content
        with open(path, 'r') as f:
            try:
                content = yaml.safe_load(f)
            except Exception as e:
                self.log.err(e)
                return {}
        return content

    @property
    def _dotfile_keys(self):
        """Return the keys of all dotfiles in this instance."""
        return map(attrgetter('key'), self.dotfiles)

    def _make_long_dotfile_key(self, path):
        """Return the long key of a dotfile, given its path splits."""
        return '_'.join(path)

    def _path_to_key_splits(self, path):
        """Split a path into dotfile key components."""
        prefix = (self.dotfile_key_file_prefix
                  if os.path.isfile(path)
                  else self.dotfile_key_directory_prefix)

        # normpath and strip(os.path.sep) prevent empty string when splitting
        path = strip_home(os.path.normpath(os.path.expanduser(path)))
        path = path.replace(' ', '-').strip(os.path.sep).lower()

        splits = [elem.lstrip('.') for elem in path.split(os.path.sep)]
        splits.insert(0, prefix)

        return splits

    def _sanitize_yaml(self, yaml_dict):
        """Remove None and set defaults for mandatory keys in YAML dicts."""
        # Clearing None values, to preserve mental sanity when checking keys
        yaml_dict = clear_none(yaml_dict)

        # Setting default to mandatory config file keys
        entries = self.default_settings.serialize()[Settings.key_yaml]
        yaml_dict.setdefault(Settings.key_yaml, entries)
        yaml_dict.setdefault(Dotfile.key_yaml, {})
        yaml_dict.setdefault(Profile.key_yaml, {})

        return yaml_dict

    def _add_dotfile(self, dotfile):
        """Add dotfile to dotfiles."""
        # Adding dotfile to Dotfile objects list
        self.dotfiles.append(dotfile)

        # Adding dotfile to YAML dictionary
        dotfile_dict = {
            Dotfile.key_src: dotfile.src,
            Dotfile.key_dst: dotfile.dst,
        }
        if dotfile.link != self.settings.link_dotfile_default:
            dotfile_dict[Dotfile.key_link] = str(dotfile.link)
        self.yaml_dict[Dotfile.key_yaml][dotfile.key] = dotfile_dict

        self._dirty = True

    def _add_dotfile_to_profile(self, dotfile, profile):
        """Add dotfile to profile."""
        # Skipping if profile already has dotfile
        if dotfile.key in profile.dotfiles:
            self.log.warn('Profile {!s} already has dotfile {!s}'
                          .format(profile, dotfile))
            return False

        # Adding dotfile key to profile dotfiles
        profile.dotfiles.append(dotfile.key)

        # Adding dotfile key to profile dotfiles in YAML dictionary
        yaml_profile = self.yaml_dict[Profile.key_yaml][profile.key]
        yaml_profile[Profile.key_dotfiles].append(dotfile.key)

        self._dirty = True

        return True

    def _add_profile(self, profile):
        """Add a profile to this YAML config file."""
        # Adding profile to profile objects
        self.profiles.append(profile)

        # Adding profile to YAML dictionary
        profile_dict = {
            Profile.key_dotfiles: profile.dotfiles,
        }
        self.yaml_dict[Profile.key_yaml][profile.key] = profile_dict

        self._dirty = True

    def _make_new_dotfile_key(self, path):
        """Return the key for a new dotfile."""
        splits = self._path_to_key_splits(path)

        key = (self._make_long_dotfile_key(splits)
               if self.settings.longkey
               else self._make_short_dotfile_key(splits))
        return self._make_unique_dotfile_key(key)

    def _make_short_dotfile_key(self, key_splits):
        """Return the short key of a dotfile, given its path splits."""
        key_paths = reversed(key_splits[1:])
        key_pieces = key_splits[:1]
        current_keys = tuple(self._dotfile_keys)

        try:
            # This runs at least once, as key_splits has at least two items:
            # the prefix and a file name
            while True:
                key_pieces.insert(1, next(key_paths))
                key = '_'.join(key_pieces)
                if key not in current_keys:
                    return key
        except StopIteration:
            # This is raised by next(key_paths): the whole dotfile path was
            # consumed wuthut finding a key not already in the current key set:
            # returning the key from last while iteration
            return key

    def _make_unique_dotfile_key(self, key):
        """Make a dotfile key unique by appending an incremental number."""
        existing_keys = tuple(self._dotfile_keys)
        if key not in existing_keys:
            return key
        return '{}_{}'.format(key, existing_keys.count(key))

    def get_dotfile(self, dst):
        """Get a dotfile by dst from this YAML config file."""
        try:
            return next(d for d in self.dotfiles if d.dst == dst)
        except StopIteration:
            return None

    def get_profile(self, key):
        """Get a profile by key from this YAML config file."""
        try:
            return next(p for p in self.profiles if p.key == key)
        except StopIteration:
            return None

    def new_dotfile(self, dotfile_args, profile_key):
        """Add a dotfile to this config YAML file."""
        if not profile_key:
            raise Exception('bad profile key: None')
        dotfile = self.get_dotfile(dotfile_args['dst'])
        if dotfile is None:
            key = self._make_new_dotfile_key(dotfile_args['dst'])
            dotfile = Dotfile(key=key, **dotfile_args)
            self._add_dotfile(dotfile)

        # add dotfile to profile
        profile = self.get_profile(profile_key)
        if profile is None:
            self.log.warn('Profile {} not found, adding it'
                          .format(profile_key))
            profile = Profile(key=profile_key)
            self._add_profile(profile)
        self._add_dotfile_to_profile(dotfile, profile)

        return True, dotfile

    def save(self, *, force=False):
        """Save this instance to the original YAML file it was parsed from."""
        if not (self._dirty or force):
            return False

        with open(self.path, 'w') as cfg_file:
            yaml.safe_dump(self.yaml_dict, cfg_file,
                           default_flow_style=False, indent=2)
        self._dirty = False
        return True
