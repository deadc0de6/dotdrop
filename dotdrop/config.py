"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

yaml config file manager
"""

import itertools
import os
import shlex
from functools import partial
from glob import iglob

import yaml

# local import
from dotdrop.dotfile import Dotfile
from dotdrop.templategen import Templategen
from dotdrop.logger import Logger
from dotdrop.action import Action, Transform
from dotdrop.utils import strip_home, shell
from dotdrop.linktypes import LinkTypes


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
    key_ignoreempty = 'ignoreempty'
    key_showdiff = 'showdiff'
    key_imp_link = 'link_on_import'
    key_dotfile_link = 'link_dotfile_default'
    key_workdir = 'workdir'
    key_cmpignore = 'cmpignore'
    key_upignore = 'upignore'
    key_defactions = 'default_actions'

    # import keys
    key_import_vars = 'import_variables'
    key_import_actions = 'import_actions'

    key_import_configs = 'import_configs'

    # actions keys
    key_actions = 'actions'
    key_actions_pre = 'pre'
    key_actions_post = 'post'

    # transformations keys
    key_trans_r = 'trans'
    key_trans_w = 'trans_write'

    # template variables
    key_variables = 'variables'
    # shell variables
    key_dynvariables = 'dynvariables'

    # dotfiles keys
    key_dotfiles = 'dotfiles'
    key_dotfiles_src = 'src'
    key_dotfiles_dst = 'dst'
    key_dotfiles_link = 'link'
    key_dotfiles_link_children = 'link_children'
    key_dotfiles_noempty = 'ignoreempty'
    key_dotfiles_cmpignore = 'cmpignore'
    key_dotfiles_actions = 'actions'
    key_dotfiles_trans_r = 'trans'
    key_dotfiles_trans_w = 'trans_write'
    key_dotfiles_upignore = 'upignore'

    # profiles keys
    key_profiles = 'profiles'
    key_profiles_dots = 'dotfiles'
    key_profiles_incl = 'include'
    key_profiles_imp = 'import'

    # link values
    lnk_nolink = LinkTypes.NOLINK.name.lower()
    lnk_link = LinkTypes.LINK.name.lower()
    lnk_children = LinkTypes.LINK_CHILDREN.name.lower()

    # settings defaults
    default_dotpath = 'dotfiles'
    default_backup = True
    default_create = True
    default_banner = True
    default_longkey = False
    default_keepdot = False
    default_showdiff = False
    default_ignoreempty = False
    default_link_imp = lnk_nolink
    default_link = lnk_nolink
    default_workdir = '~/.config/dotdrop'

    def __init__(self, cfgpath, profile=None, debug=False):
        """constructor
        @cfgpath: path to the config file
        @profile: chosen profile
        @debug: enable debug
        """
        if not cfgpath:
            raise ValueError('config file path undefined')
        if not os.path.exists(cfgpath):
            raise ValueError('config file does not exist: {}'.format(cfgpath))

        # make sure to have an absolute path to config file
        self.cfgpath = os.path.abspath(cfgpath)
        self.debug = debug
        self._modified = False

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

        # dict of all read transformation objects by trans key
        # NOT linked inside the yaml dict (self.content)
        self.trans_r = {}

        # dict of all write transformation objects by trans key
        # NOT linked inside the yaml dict (self.content)
        self.trans_w = {}

        # represents all dotfiles per profile by profile key
        # NOT linked inside the yaml dict (self.content)
        self.prodots = {}

        # represents all variables from external files
        # NOT linked inside the yaml dict (self.content)
        self.ext_variables = {}
        self.ext_dynvariables = {}

        # cmpignore patterns
        # NOT linked inside the yaml dict (self.content)
        self.cmpignores = []

        # upignore patterns
        # NOT linked inside the yaml dict (self.content)
        self.upignores = []

        # default actions
        # NOT linked inside the yaml dict (self.content)
        self.defactions = {}

        if not self._load_config(profile=profile):
            raise ValueError('config is not valid')

    def __eq__(self, other):
        return self.cfgpath == other.cfgpath

    def eval_dotfiles(self, profile, variables, debug=False):
        """resolve dotfiles src/dst/actions templating for this profile"""
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

    def _load_config(self, profile=None):
        """load the yaml file"""
        self.content = self._load_yaml(self.cfgpath)
        if not self._is_valid():
            return False
        return self._parse(profile=profile)

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
        return True

    def _get_def_link(self):
        """get dotfile link entry when not specified"""
        string = self.lnk_settings[self.key_dotfile_link].lower()
        return self._string_to_linktype(string)

    def _string_to_linktype(self, string):
        """translate string to linktype"""
        if string == self.lnk_link.lower():
            return LinkTypes.LINK
        elif string == self.lnk_children.lower():
            return LinkTypes.LINK_CHILDREN
        return LinkTypes.NOLINK

    def _parse(self, profile=None):
        """parse config file"""
        # parse the settings
        self.lnk_settings = self.content[self.key_settings] or {}
        if not self._complete_settings():
            return False

        # parse the profiles
        # ensures self.lnk_profiles is a dict
        if not isinstance(self.content[self.key_profiles], dict):
            self.content[self.key_profiles] = {}

        self.lnk_profiles = self.content[self.key_profiles]
        for p in filter(bool, self.lnk_profiles.values()):
            # Ensures that the dotfiles entry is an empty list when not given
            # or none
            p.setdefault(self.key_profiles_dots, [])
            if p[self.key_profiles_dots] is None:
                p[self.key_profiles_dots] = []

        # make sure we have an absolute dotpath
        self.curdotpath = self.lnk_settings[self.key_dotpath]
        self.lnk_settings[self.key_dotpath] = self._abs_path(self.curdotpath)

        # make sure we have an absolute workdir
        self.curworkdir = self.lnk_settings[self.key_workdir]
        self.lnk_settings[self.key_workdir] = self._abs_path(self.curworkdir)

        # load external variables/dynvariables
        try:
            paths = self.lnk_settings[self.key_import_vars] or []
            self._load_ext_variables(paths, profile=profile)
        except KeyError:
            pass

        # load global upignore
        if self.key_upignore in self.lnk_settings:
            key = self.key_upignore
            self.upignores = self.lnk_settings[key].copy() or []

        # load global cmpignore
        if self.key_cmpignore in self.lnk_settings:
            key = self.key_cmpignore
            self.cmpignores = self.lnk_settings[key].copy() or []

        # parse external actions
        try:
            ext_actions = self.lnk_settings[self.key_import_actions] or ()
            for path in ext_actions:
                path = self._abs_path(path)
                if self.debug:
                    self.log.dbg('loading actions from {}'.format(path))
                content = self._load_yaml(path)
                # If external actions are None, replaces them with empty dict
                try:
                    external_actions = content[self.key_actions] or {}
                    self._load_actions(external_actions)
                except KeyError:
                    pass
        except KeyError:
            pass

        # parse external configs
        try:
            ext_configs = self.lnk_settings[self.key_import_configs] or ()

            try:
                iglob('./*', recursive=True)
                find_glob = partial(iglob, recursive=True)
            except TypeError:
                from platform import python_version

                msg = ('Recursive globbing is not available on Python {}: '
                       .format(python_version()))
                if any('**' in config for config in ext_configs):
                    msg += "import_configs won't work"
                    self.log.err(msg)
                    return False

                msg = 'upgrade to version >3.5 if you want to use this feature'
                self.log.warn(msg)
                find_glob = iglob

            ext_configs = itertools.chain.from_iterable(
                find_glob(self._abs_path(config))
                for config in ext_configs
            )
            for config in ext_configs:
                self._merge_cfg(config)
        except KeyError:
            pass

        # parse local actions
        # If local actions are None, replaces them with empty dict
        try:
            local_actions = self.content[self.key_actions] or {}
            self._load_actions(local_actions)
        except KeyError:
            pass

        # load default actions
        try:
            dactions = self.lnk_settings[self.key_defactions].copy() or []
            self.defactions = self._parse_actions_list(dactions,
                                                       profile=profile)
        except KeyError:
            self.defactions = {
                self.key_actions_pre: [],
                self.key_actions_post: [],
            }

        # parse read transformations
        # If read transformations are None, replaces them with empty dict
        try:
            read_trans = self.content[self.key_trans_r] or {}
            self.trans_r.update({
                k: Transform(k, v)
                for k, v
                in read_trans.items()
            })
        except KeyError:
            pass

        # parse write transformations
        # If write transformations are None, replaces them with empty dict
        try:
            read_trans = self.content[self.key_trans_w] or {}
            self.trans_w.update({
                k: Transform(k, v)
                for k, v
                in read_trans.items()
            })
        except KeyError:
            pass

        # parse the dotfiles and construct the dict of objects per dotfile key
        # ensures the dotfiles entry is a dict
        if not isinstance(self.content[self.key_dotfiles], dict):
            self.content[self.key_dotfiles] = {}

        dotfiles = self.content[self.key_dotfiles]
        noempty_default = self.lnk_settings[self.key_ignoreempty]
        dotpath = self.lnk_settings[self.key_dotpath]
        for k, v in dotfiles.items():
            src = v[self.key_dotfiles_src]
            if dotpath not in src:
                src = os.path.join(dotpath, src)
            src = os.path.normpath(self._abs_path(src))
            dst = os.path.normpath(v[self.key_dotfiles_dst])

            # Fail if both `link` and `link_children` present
            if self.key_dotfiles_link in v \
                    and self.key_dotfiles_link_children in v:
                msg = 'only one of `link` or `link_children` allowed per'
                msg += ' dotfile, error on dotfile "{}".'
                self.log.err(msg.format(k))
                return False

            # fix it
            v = self._fix_dotfile_link(k, v)
            dotfiles[k] = v

            # get link type
            link = self._get_def_link()
            if self.key_dotfiles_link in v:
                link = self._string_to_linktype(v[self.key_dotfiles_link])

            # get ignore empty
            noempty = v.get(self.key_dotfiles_noempty, noempty_default)

            # parse actions
            itsactions = v.get(self.key_dotfiles_actions, [])
            actions = self._parse_actions_list(itsactions, profile=profile)
            if self.debug:
                self.log.dbg('action for {}'.format(k))
                for t in [self.key_actions_pre, self.key_actions_post]:
                    for action in actions[t]:
                        self.log.dbg('- {}: {}'.format(t, action))

            # parse read transformation
            itstrans_r = v.get(self.key_dotfiles_trans_r)
            trans_r = None
            if itstrans_r:
                if type(itstrans_r) is list:
                    msg = 'One transformation allowed per dotfile'
                    msg += ', error on dotfile \"{}\"'
                    self.log.err(msg.format(k))
                    msg = 'Please modify your config file to: \"trans: {}\"'
                    self.log.err(msg.format(itstrans_r[0]))
                    return False
                trans_r = self._parse_trans(itstrans_r, read=True)
                if not trans_r:
                    msg = 'unknown trans \"{}\" for \"{}\"'
                    self.log.err(msg.format(itstrans_r, k))
                    return False

            # parse write transformation
            itstrans_w = v.get(self.key_dotfiles_trans_w)
            trans_w = None
            if itstrans_w:
                if type(itstrans_w) is list:
                    msg = 'One write transformation allowed per dotfile'
                    msg += ', error on dotfile \"{}\"'
                    self.log.err(msg.format(k))
                    msg = 'Please modify your config file: \"trans_write: {}\"'
                    self.log.err(msg.format(itstrans_w[0]))
                    return False
                trans_w = self._parse_trans(itstrans_w, read=False)
                if not trans_w:
                    msg = 'unknown trans_write \"{}\" for \"{}\"'
                    self.log.err(msg.format(itstrans_w, k))
                    return False

            # disable transformation when link is true
            if link != LinkTypes.NOLINK and (trans_r or trans_w):
                msg = 'transformations disabled for \"{}\"'.format(dst)
                msg += ' because link|link_children is enabled'
                self.log.warn(msg)
                trans_r = None
                trans_w = None

            # parse cmpignore pattern
            cmpignores = v.get(self.key_dotfiles_cmpignore, []).copy()
            cmpignores.extend(self.cmpignores)

            # parse upignore pattern
            upignores = v.get(self.key_dotfiles_upignore, []).copy()
            upignores.extend(self.upignores)

            # create new dotfile
            self.dotfiles[k] = Dotfile(k, dst, src,
                                       link=link, actions=actions,
                                       trans_r=trans_r, trans_w=trans_w,
                                       cmpignore=cmpignores, noempty=noempty,
                                       upignore=upignores)

        # assign dotfiles to each profile
        self.prodots = {k: [] for k in self.lnk_profiles.keys()}
        for name, profile in self.lnk_profiles.items():
            if not profile:
                continue
            dots = profile[self.key_profiles_dots]
            if not dots:
                continue

            if self.key_all in dots:
                # add all if key ALL is used
                self.prodots[name] = list(self.dotfiles.values())
            else:
                # add the dotfiles
                for d in dots:
                    if d not in self.dotfiles:
                        msg = 'unknown dotfile \"{}\" for {}'.format(d, k)
                        self.log.err(msg)
                        continue
                    self.prodots[name].append(self.dotfiles[d])

        profile_names = self.lnk_profiles.keys()
        # handle "import" (from file) for each profile
        for k in profile_names:
            dots = self._get_imported_dotfiles_keys(k)
            for d in dots:
                if d not in self.dotfiles:
                    msg = '(i) unknown dotfile \"{}\" for {}'.format(d, k)
                    self.log.err(msg)
                    continue
                self.prodots[k].append(self.dotfiles[d])

        # handle "include" (from other profile) for each profile
        for k in profile_names:
            ret, dots = self._get_included_dotfiles(k)
            if not ret:
                return False
            self.prodots[k].extend(dots)

        # remove duplicates if any
        self.prodots = {k: list(set(v)) for k, v in self.prodots.items()}

        # print dotfiles for each profile
        if self.debug:
            for k in self.lnk_profiles.keys():
                df = ','.join(d.key for d in self.prodots[k])
                self.log.dbg('dotfiles for \"{}\": {}'.format(k, df))
        return True

    def _merge_dict(self, ext_config, warning_prefix, self_member,
                    ext_member=None, traceback=False):
        """Merge into self a dictionary instance members from an external Cfg.

        This method merges instance members of another Cfg instance into self.
        It issues a warning for any key shared between self and the other Cfg.
        It can adds an own=False porperty to any dictionary in the external
        instance member before merging.

        :param ext_config: The other Cfg to merge from.
        :type ext_config: Cfg
        :param warnign_prefix: The prefix to th warning messages.
        :type warning_prefix: str
        :param self_member: The member of self which will be augmented by the
            external member. Or the self_member name as a string.
        :type self_member: dict or str
        :param ext_member: The member of ext_config which wil be merged in
            self_member. When not given, self_member is assumed to be a string,
            and self_member and ext_member are supposed to have the same name.
        :type ext_member: dict or None
        :param traceback: Whether to add own=False to ext_member dict values
            before merging in.
        :type traceback: bool

        """
        if ext_member is None:
            member_name = self_member
            self_member = getattr(self, member_name)
            ext_member = getattr(ext_config, member_name)

        common_keys = (
            key
            for key in (set(self_member.keys())
                        .intersection(set(ext_member.keys())))
            if not key.startswith('_')  # filtering out internal variables
        )
        warning_msg = ('%s {} defined both in %s and %s: {} in %s used'
                       % (warning_prefix, self.cfgpath, ext_config.cfgpath,
                          self.cfgpath))
        for key in common_keys:
            self.log.warn(warning_msg.format(key, key))

        if traceback:
            # Assumes v to be a dict. So far it's only used for profiles,
            # that are in fact dicts
            merged = {
                k: dict(v, own=False)
                for k, v in ext_member.items()
            }
        else:
            merged = ext_member.copy()
        merged.update(self_member)
        self_member.update(merged)

        return self_member

    def _merge_cfg(self, config_path):
        """Merge an external config.yaml file into self."""
        # Parsing external config file
        try:
            ext_config = Cfg(config_path)
        except ValueError:
            raise ValueError(
                'external config file not found: {}'.format(config_path))

        # Merging in members from the external config file
        self._merge_dict(ext_config=ext_config, warning_prefix='Dotfile',
                         self_member='dotfiles')
        self._merge_dict(ext_config=ext_config, warning_prefix='Profile',
                         self_member='lnk_profiles', traceback=True)
        self._merge_dict(ext_config=ext_config, warning_prefix='Action',
                         self_member='actions')
        self._merge_dict(ext_config=ext_config,
                         warning_prefix='Transformation',
                         self_member='trans_r')
        self._merge_dict(ext_config=ext_config,
                         warning_prefix='Write transformation',
                         self_member='trans_w')
        self._merge_dict(ext_config=ext_config, warning_prefix='Profile',
                         self_member='prodots')

        # variables are merged in ext_*variables so as not to be added in
        # self.content. This needs an additional step to account for imported
        # variables sharing a key with the ones defined in self.content.
        variables = {
            k: v
            for k, v in ext_config._get_variables(None).items()
            if k not in self.content[self.key_variables]
        }
        dyn_variables = {
            k: v
            for k, v in ext_config._get_dynvariables(None).items()
            if k not in self.content[self.key_dynvariables]
        }
        self._merge_dict(ext_config=ext_config, warning_prefix='Variable',
                         self_member=self.ext_variables,
                         ext_member=variables)
        self._merge_dict(ext_config=ext_config,
                         warning_prefix='Dynamic variable',
                         self_member=self.ext_dynvariables,
                         ext_member=dyn_variables)

    def _load_ext_variables(self, paths, profile=None):
        """load external variables"""
        variables = {}
        dvariables = {}
        cur_vars = self.get_variables(profile, debug=self.debug)
        t = Templategen(variables=cur_vars)
        for path in paths:
            path = self._abs_path(path)
            path = t.generate_string(path)
            if self.debug:
                self.log.dbg('loading variables from {}'.format(path))
            content = self._load_yaml(path)
            if not content:
                self.log.warn('\"{}\" does not exist'.format(path))
                continue
            # variables
            if self.key_variables in content:
                variables.update(content[self.key_variables])
            # dynamic variables
            if self.key_dynvariables in content:
                dvariables.update(content[self.key_dynvariables])
        self.ext_variables = variables
        if self.debug:
            self.log.dbg('loaded ext variables: {}'.format(variables))
        self.ext_dynvariables = dvariables
        if self.debug:
            self.log.dbg('loaded ext dynvariables: {}'.format(dvariables))

    def _load_actions(self, dic):
        for k, v in dic.items():
            # loop through all actions
            if k in [self.key_actions_pre, self.key_actions_post]:
                # parse pre/post actions
                items = dic[k].items()
                for k2, v2 in items:
                    if k not in self.actions:
                        self.actions[k] = {}
                    a = Action(k2, k, v2)
                    self.actions[k][k2] = a
                    if self.debug:
                        self.log.dbg('new action: {}'.format(a))
            else:
                # parse naked actions as post actions
                if self.key_actions_post not in self.actions:
                    self.actions[self.key_actions_post] = {}
                a = Action(k, '', v)
                self.actions[self.key_actions_post][k] = a
                if self.debug:
                    self.log.dbg('new action: {}'.format(a))

    def _abs_path(self, path):
        """return absolute path of path relative to the confpath"""
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            d = os.path.dirname(self.cfgpath)
            return os.path.join(d, path)
        return path

    def _get_imported_dotfiles_keys(self, profile):
        """import dotfiles from external file"""
        keys = []
        if self.key_profiles_imp not in self.lnk_profiles[profile]:
            return keys
        variables = self.get_variables(profile, debug=self.debug)
        t = Templategen(variables=variables)
        paths = self.lnk_profiles[profile][self.key_profiles_imp]
        for path in paths:
            path = self._abs_path(path)
            path = t.generate_string(path)
            if self.debug:
                self.log.dbg('loading dotfiles from {}'.format(path))
            content = self._load_yaml(path)
            if not content:
                self.log.warn('\"{}\" does not exist'.format(path))
                continue
            if self.key_profiles_dots not in content:
                self.log.warn('not dotfiles in \"{}\"'.format(path))
                continue
            df = content[self.key_profiles_dots]
            if self.debug:
                self.log.dbg('imported dotfiles keys: {}'.format(df))
            keys.extend(df)
        return keys

    def _get_included_dotfiles(self, profile, seen=[]):
        """find all dotfiles for a specific profile
        when using the include keyword"""
        if profile in seen:
            self.log.err('cyclic include in profile \"{}\"'.format(profile))
            return False, []
        if not self.lnk_profiles[profile]:
            return True, []
        dotfiles = self.prodots[profile]
        if self.key_profiles_incl not in self.lnk_profiles[profile]:
            # no include found
            return True, dotfiles
        if not self.lnk_profiles[profile][self.key_profiles_incl]:
            # empty include found
            return True, dotfiles
        variables = self.get_variables(profile, debug=self.debug)
        t = Templategen(variables=variables)
        if self.debug:
            self.log.dbg('handle includes for profile \"{}\"'.format(profile))
        for other in self.lnk_profiles[profile][self.key_profiles_incl]:
            # resolve include value
            other = t.generate_string(other)
            if other not in self.prodots:
                # no such profile
                self.log.warn('unknown included profile \"{}\"'.format(other))
                continue
            if self.debug:
                msg = 'include dotfiles from \"{}\" into \"{}\"'
                self.log.dbg(msg.format(other, profile))
            lseen = seen.copy()
            lseen.append(profile)
            ret, recincludes = self._get_included_dotfiles(other, seen=lseen)
            if not ret:
                return False, []
            dotfiles.extend(recincludes)
            dotfiles.extend(self.prodots[other])
        return True, dotfiles

    def _parse_actions_list(self, entries, profile=None):
        """parse actions specified for an element
        where entries are the ones defined for this dotfile"""
        res = {
            self.key_actions_pre: [],
            self.key_actions_post: [],
        }
        vars = self.get_variables(profile, debug=self.debug)
        t = Templategen(variables=vars)
        for line in entries:
            fields = shlex.split(line)
            entry = fields[0]
            args = []
            if len(fields) > 1:
                tmpargs = fields[1:]
                args = []
                # template args
                for arg in tmpargs:
                    args.append(t.generate_string(arg))
            action = None
            if self.key_actions_pre in self.actions and \
                    entry in self.actions[self.key_actions_pre]:
                kind = self.key_actions_pre
                if not args:
                    action = self.actions[self.key_actions_pre][entry]
                else:
                    a = self.actions[self.key_actions_pre][entry].action
                    action = Action(entry, kind, a, *args)
            elif self.key_actions_post in self.actions and \
                    entry in self.actions[self.key_actions_post]:
                kind = self.key_actions_post
                if not args:
                    action = self.actions[self.key_actions_post][entry]
                else:
                    a = self.actions[self.key_actions_post][entry].action
                    action = Action(entry, kind, a, *args)
            else:
                self.log.warn('unknown action \"{}\"'.format(entry))
                continue
            res[kind].append(action)
        return res

    def _parse_trans(self, trans, read=True):
        """parse transformation key specified for a dotfile"""
        transformations = self.trans_r
        if not read:
            transformations = self.trans_w
        if trans not in transformations.keys():
            return None
        return transformations[trans]

    def _complete_settings(self):
        """set settings defaults if not present"""
        self._fix_deprecated()
        if self.key_dotpath not in self.lnk_settings:
            self.lnk_settings[self.key_dotpath] = self.default_dotpath
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
        if self.key_workdir not in self.lnk_settings:
            self.lnk_settings[self.key_workdir] = self.default_workdir
        if self.key_showdiff not in self.lnk_settings:
            self.lnk_settings[self.key_showdiff] = self.default_showdiff
        if self.key_ignoreempty not in self.lnk_settings:
            self.lnk_settings[self.key_ignoreempty] = self.default_ignoreempty

        if self.key_dotfile_link not in self.lnk_settings:
            self.lnk_settings[self.key_dotfile_link] = self.default_link
        else:
            key = self.lnk_settings[self.key_dotfile_link]
            if key != self.lnk_link and \
                    key != self.lnk_children and \
                    key != self.lnk_nolink:
                self.log.err('bad value for {}'.format(self.key_dotfile_link))
                return False

        if self.key_imp_link not in self.lnk_settings:
            self.lnk_settings[self.key_imp_link] = self.default_link_imp
        else:
            key = self.lnk_settings[self.key_imp_link]
            if key != self.lnk_link and \
                    key != self.lnk_children and \
                    key != self.lnk_nolink:
                self.log.err('bad value for {}'.format(self.key_dotfile_link))
                return False
        return True

    def _fix_deprecated(self):
        """fix deprecated entries"""
        # link_by_default
        key = 'link_by_default'
        newkey = self.key_imp_link
        if key in self.lnk_settings:
            if self.lnk_settings[key]:
                self.lnk_settings[newkey] = self.lnk_link
            else:
                self.lnk_settings[newkey] = self.lnk_nolink
            del self.lnk_settings[key]
            self._modified = True

    def _fix_dotfile_link(self, key, entry):
        """fix deprecated link usage in dotfile entry"""
        v = entry

        if self.key_dotfiles_link not in v \
                and self.key_dotfiles_link_children not in v:
            # nothing defined
            return v

        new = self.lnk_nolink
        if self.key_dotfiles_link in v \
                and type(v[self.key_dotfiles_link]) is bool:
            # patch link: <bool>
            if v[self.key_dotfiles_link]:
                new = self.lnk_link
            else:
                new = self.lnk_nolink
            self._modified = True
            if self.debug:
                self.log.dbg('link updated for {} to {}'.format(key, new))
        elif self.key_dotfiles_link_children in v \
                and type(v[self.key_dotfiles_link_children]) is bool:
            # patch link_children: <bool>
            if v[self.key_dotfiles_link_children]:
                new = self.lnk_children
            else:
                new = self.lnk_nolink
            del v[self.key_dotfiles_link_children]
            self._modified = True
            if self.debug:
                self.log.dbg('link updated for {} to {}'.format(key, new))
        else:
            # no change
            new = v[self.key_dotfiles_link]

        v[self.key_dotfiles_link] = new
        return v

    @classmethod
    def _filter_not_own(cls, content):
        """Filters out from a dict its dict values with own=False."""
        # This way it recursively explores only dicts. Since own=False is used
        # only in profiles, which are in fact dicts, this is fine for now.
        return {
            k: cls._filter_not_own(v) if isinstance(v, dict) else v
            for k, v in content.items()
            if not isinstance(v, dict) or v.get('own', True)
        }

    def _save(self, content, path):
        """writes the config to file"""
        ret = False
        with open(path, 'w') as f:
            ret = yaml.safe_dump(self._filter_not_own(content), f,
                                 default_flow_style=False,
                                 indent=2)
        if ret:
            self._modified = False
        return ret

    def _norm_key_elem(self, elem):
        """normalize path element for sanity"""
        elem = elem.lstrip('.')
        elem = elem.replace(' ', '-')
        return elem.lower()

    def _get_paths(self, path):
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
        dirs = list(map(self._norm_key_elem, dirs))
        return dirs

    def _get_long_key(self, path, keys):
        """return a unique long key representing the
        absolute path of path"""
        dirs = self._get_paths(path)
        # prepend with indicator
        if os.path.isdir(path):
            key = 'd_{}'.format('_'.join(dirs))
        else:
            key = 'f_{}'.format('_'.join(dirs))
        return self._get_unique_key(key, keys)

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
                return key
        return self._get_unique_key(key, keys)

    def _get_unique_key(self, key, keys):
        """return a unique dotfile key"""
        newkey = key
        cnt = 1
        while newkey in keys:
            # if unable to get a unique path
            # get a random one
            newkey = '{}_{}'.format(key, cnt)
            cnt += 1
        return newkey

    def _dotfile_exists(self, dotfile):
        """return True and the existing dotfile key
        if it already exists, False and a new unique key otherwise"""
        try:
            return True, next(key
                              for key, d in self.dotfiles.items()
                              if d.dst == dotfile.dst)
        except StopIteration:
            pass
        # return key for this new dotfile
        path = os.path.expanduser(dotfile.dst)
        keys = self.dotfiles.keys()
        if self.lnk_settings[self.key_long]:
            return False, self._get_long_key(path, keys)
        return False, self._get_short_key(path, keys)

    def new(self, src, dst, profile, link, debug=False):
        """import new dotfile"""
        # keep it short
        home = os.path.expanduser('~')
        dst = dst.replace(home, '~', 1)
        dotfile = Dotfile('', dst, src)

        # adding new profile if doesn't exist
        if profile not in self.lnk_profiles:
            if debug:
                self.log.dbg('adding profile to config')
            # in the yaml
            self.lnk_profiles[profile] = {self.key_profiles_dots: []}
            # in the global list of dotfiles per profile
            self.prodots[profile] = []

        exists, key = self._dotfile_exists(dotfile)
        if exists:
            if debug:
                self.log.dbg('key already exists: {}'.format(key))
            # retrieve existing dotfile
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

        if debug:
            self.log.dbg('dotfile attributed key: {}'.format(key))
        # adding the new dotfile
        dotfile.key = key
        dotfile.link = link
        if debug:
            self.log.dbg('adding new dotfile: {}'.format(dotfile))
        # add the entry in the yaml file
        dots = self.content[self.key_dotfiles]
        dots[dotfile.key] = {
            self.key_dotfiles_dst: dotfile.dst,
            self.key_dotfiles_src: dotfile.src,
        }

        # set the link flag
        if link != self._get_def_link():
            val = link.name.lower()
            dots[dotfile.key][self.key_dotfiles_link] = val

        # link it to this profile in the yaml file
        pro = self.content[self.key_profiles][profile]
        if self.key_all not in pro[self.key_profiles_dots]:
            pro[self.key_profiles_dots].append(dotfile.key)

        # add it to the global list of dotfiles
        self.dotfiles[dotfile.key] = dotfile
        # add it to this profile
        self.prodots[profile].append(dotfile)

        return True, dotfile

    def _get_dotfiles(self, profile):
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
        settings = self.lnk_settings.copy()
        # patch link entries
        key = self.key_imp_link
        settings[key] = self._string_to_linktype(settings[key])
        key = self.key_dotfile_link
        settings[key] = self._string_to_linktype(settings[key])
        # patch defactions
        key = self.key_defactions
        settings[key] = self.defactions
        return settings

    def get_variables(self, profile, debug=False):
        """return the variables for this profile"""
        # get flat variables
        variables = self._get_variables(profile=profile)

        # get interpreted variables
        dvariables = self._get_dynvariables(profile)

        # recursive resolve variables
        allvars = variables.copy()
        allvars.update(dvariables)
        var = self._rec_resolve_vars(allvars)

        # execute dynvariables
        for k in dvariables.keys():
            var[k] = shell(var[k])

        if debug:
            self.log.dbg('variables:')
            for k, v in var.items():
                self.log.dbg('\t\"{}\": {}'.format(k, v))

        return var

    def _rec_resolve_vars(self, variables):
        """recursive resolve all variables"""
        t = Templategen(variables=variables)

        for k in variables.keys():
            val = variables[k]
            while Templategen.var_is_template(val):
                val = t.generate_string(val)
                variables[k] = val
                t.update_variables(variables)
        return variables

    def _get_variables(self, profile=None):
        """return the un-interpreted variables"""
        variables = {}

        # profile variable
        if profile:
            variables['profile'] = profile

        # add paths variables
        variables['_dotdrop_dotpath'] = self.lnk_settings[self.key_dotpath]
        variables['_dotdrop_cfgpath'] = self.cfgpath
        variables['_dotdrop_workdir'] = self.lnk_settings[self.key_workdir]

        # global variables
        if self.key_variables in self.content:
            variables.update(self.content[self.key_variables])

        # external variables
        variables.update(self.ext_variables)

        if not profile or profile not in self.lnk_profiles:
            return variables

        # profile variables
        var = self.lnk_profiles[profile]
        if self.key_variables in var.keys():
            for k, v in var[self.key_variables].items():
                variables[k] = v

        return variables

    def _get_dynvariables(self, profile):
        """return the dyn variables"""
        variables = {}

        # global dynvariables
        if self.key_dynvariables in self.content:
            # interpret dynamic variables
            variables.update(self.content[self.key_dynvariables])

        # external variables
        variables.update(self.ext_dynvariables)

        if profile not in self.lnk_profiles:
            return variables

        # profile dynvariables
        var = self.lnk_profiles[profile]
        if self.key_dynvariables in var.keys():
            variables.update(var[self.key_dynvariables])

        return variables

    def dump(self):
        """return a dump of the config"""
        # temporary reset paths
        dotpath = self.lnk_settings[self.key_dotpath]
        workdir = self.lnk_settings[self.key_workdir]
        self.lnk_settings[self.key_dotpath] = self.curdotpath
        self.lnk_settings[self.key_workdir] = self.curworkdir
        # dump
        ret = yaml.safe_dump(self.content,
                             default_flow_style=False,
                             indent=2)
        ret = ret.replace('{}', '')
        # restore paths
        self.lnk_settings[self.key_dotpath] = dotpath
        self.lnk_settings[self.key_workdir] = workdir
        return ret

    def is_modified(self):
        """need the db to be saved"""
        return self._modified

    def save(self):
        """save the config to file"""
        # temporary reset paths
        dotpath = self.lnk_settings[self.key_dotpath]
        workdir = self.lnk_settings[self.key_workdir]
        self.lnk_settings[self.key_dotpath] = self.curdotpath
        self.lnk_settings[self.key_workdir] = self.curworkdir
        # save
        ret = self._save(self.content, self.cfgpath)
        # restore path
        self.lnk_settings[self.key_dotpath] = dotpath
        self.lnk_settings[self.key_workdir] = workdir
        return ret
