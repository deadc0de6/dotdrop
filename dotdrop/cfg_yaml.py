"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

handle lower level of the config file
"""

import os
from ruamel.yaml import YAML as yaml
import glob
from copy import deepcopy

# local imports
from dotdrop.settings import Settings
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
from dotdrop.linktypes import LinkTypes
from dotdrop.utils import shell, uniq_list
from dotdrop.exceptions import YamlException


class CfgYaml:

    # global entries
    key_settings = 'config'
    key_dotfiles = 'dotfiles'
    key_profiles = 'profiles'
    key_actions = 'actions'
    old_key_trans_r = 'trans'
    key_trans_r = 'trans_read'
    key_trans_w = 'trans_write'
    key_variables = 'variables'
    key_dvariables = 'dynvariables'

    action_pre = 'pre'
    action_post = 'post'

    # profiles/dotfiles entries
    key_dotfile_src = 'src'
    key_dotfile_dst = 'dst'
    key_dotfile_link = 'link'
    key_dotfile_actions = 'actions'
    key_dotfile_link_children = 'link_children'
    key_dotfile_noempty = 'ignoreempty'

    # profile
    key_profile_dotfiles = 'dotfiles'
    key_profile_include = 'include'
    key_profile_variables = 'variables'
    key_profile_dvariables = 'dynvariables'
    key_profile_actions = 'actions'
    key_all = 'ALL'

    # import entries
    key_import_actions = 'import_actions'
    key_import_configs = 'import_configs'
    key_import_variables = 'import_variables'
    key_import_profile_dfs = 'import'

    # settings
    key_settings_dotpath = 'dotpath'
    key_settings_workdir = 'workdir'
    key_settings_link_dotfile_default = 'link_dotfile_default'
    key_settings_noempty = 'ignoreempty'
    key_imp_link = 'link_on_import'

    # link values
    lnk_nolink = LinkTypes.NOLINK.name.lower()
    lnk_link = LinkTypes.LINK.name.lower()
    lnk_children = LinkTypes.LINK_CHILDREN.name.lower()

    def __init__(self, path, profile=None, debug=False):
        """
        config parser
        @path: config file path
        @profile: the selected profile
        @debug: debug flag
        """
        self.path = os.path.abspath(path)
        self.profile = profile
        self.debug = debug
        self.log = Logger()
        self.dirty = False

        if not os.path.exists(path):
            err = 'invalid config path: \"{}\"'.format(path)
            if self.debug:
                self.log.dbg(err)
            raise YamlException(err)

        self.yaml_dict = self._load_yaml(self.path)
        # live patch deprecated entries
        self._fix_deprecated(self.yaml_dict)
        # parse to self variables
        self._parse_main_yaml(self.yaml_dict)
        if self.debug:
            self.log.dbg('before normalization: {}'.format(self.yaml_dict))

        # resolve variables
        self.variables, self.prokeys = self._merge_variables()

        # apply variables
        self._apply_variables()

        # process imported variables (import_variables)
        self._import_variables()
        # process imported actions (import_actions)
        self._import_actions()
        # process imported profile dotfiles (import)
        self._import_profiles_dotfiles()
        # process imported configs (import_configs)
        self._import_configs()

        # process profile include
        self._resolve_profile_includes()
        # process profile ALL
        self._resolve_profile_all()
        # patch dotfiles paths
        self._resolve_dotfile_paths()

        if self.debug:
            self.log.dbg('after normalization: {}'.format(self.yaml_dict))

    def get_variables(self):
        """retrieve all variables"""
        return self.variables

    ########################################################
    # parsing
    ########################################################

    def _parse_main_yaml(self, dic):
        """parse the different blocks"""
        self.ori_settings = self._get_entry(dic, self.key_settings)
        self.settings = Settings(None).serialize().get(self.key_settings)
        self.settings.update(self.ori_settings)

        # resolve settings paths
        p = self._norm_path(self.settings[self.key_settings_dotpath])
        self.settings[self.key_settings_dotpath] = p
        p = self._norm_path(self.settings[self.key_settings_workdir])
        self.settings[self.key_settings_workdir] = p
        if self.debug:
            self.log.dbg('settings: {}'.format(self.settings))

        # dotfiles
        self.ori_dotfiles = self._get_entry(dic, self.key_dotfiles)
        self.dotfiles = deepcopy(self.ori_dotfiles)
        keys = self.dotfiles.keys()
        if len(keys) != len(list(set(keys))):
            dups = [x for x in keys if x not in list(set(keys))]
            err = 'duplicate dotfile keys found: {}'.format(dups)
            raise YamlException(err)
        self.dotfiles = self._norm_dotfiles(self.dotfiles)
        if self.debug:
            self.log.dbg('dotfiles: {}'.format(self.dotfiles))

        # profiles
        self.ori_profiles = self._get_entry(dic, self.key_profiles)
        self.profiles = deepcopy(self.ori_profiles)
        self.profiles = self._norm_profiles(self.profiles)
        if self.debug:
            self.log.dbg('profiles: {}'.format(self.profiles))

        # actions
        self.ori_actions = self._get_entry(dic, self.key_actions,
                                           mandatory=False)
        self.actions = deepcopy(self.ori_actions)
        self.actions = self._norm_actions(self.actions)
        if self.debug:
            self.log.dbg('actions: {}'.format(self.actions))

        # trans_r
        key = self.key_trans_r
        if self.old_key_trans_r in dic:
            self.log.warn('\"trans\" is deprecated, please use \"trans_read\"')
            dic[self.key_trans_r] = dic[self.old_key_trans_r]
            del dic[self.old_key_trans_r]
        self.ori_trans_r = self._get_entry(dic, key, mandatory=False)
        self.trans_r = deepcopy(self.ori_trans_r)
        if self.debug:
            self.log.dbg('trans_r: {}'.format(self.trans_r))

        # trans_w
        self.ori_trans_w = self._get_entry(dic, self.key_trans_w,
                                           mandatory=False)
        self.trans_w = deepcopy(self.ori_trans_w)
        if self.debug:
            self.log.dbg('trans_w: {}'.format(self.trans_w))

        # variables
        self.ori_variables = self._get_entry(dic,
                                             self.key_variables,
                                             mandatory=False)
        if self.debug:
            self.log.dbg('variables: {}'.format(self.ori_variables))

        # dynvariables
        self.ori_dvariables = self._get_entry(dic,
                                              self.key_dvariables,
                                              mandatory=False)
        if self.debug:
            self.log.dbg('dynvariables: {}'.format(self.ori_dvariables))

    def _resolve_dotfile_paths(self):
        """resolve dotfile paths"""
        for dotfile in self.dotfiles.values():
            src = dotfile[self.key_dotfile_src]
            src = os.path.join(self.settings[self.key_settings_dotpath], src)
            dotfile[self.key_dotfile_src] = self._norm_path(src)
            dst = dotfile[self.key_dotfile_dst]
            dotfile[self.key_dotfile_dst] = self._norm_path(dst)

    def _rec_resolve_vars(self, variables):
        """recursive resolve variables"""
        t = Templategen(variables=variables)
        for k in variables.keys():
            val = variables[k]
            while Templategen.var_is_template(val):
                val = t.generate_string(val)
                variables[k] = val
                t.update_variables(variables)
        return variables

    def _merge_variables(self):
        """
        resolve all variables across the config
        apply them to any needed entries
        and return the full list of variables
        """
        if self.debug:
            self.log.dbg('get local variables')

        # get all variables from local and resolve
        var = self._get_variables_dict(self.profile)

        # get all dynvariables from local and resolve
        dvar = self._get_dvariables_dict()

        # temporarly resolve all variables for "include"
        merged = self._merge_dict(dvar, var)
        merged = self._rec_resolve_vars(merged)
        self._debug_vars(merged)
        # exec dynvariables
        self._shell_exec_dvars(dvar.keys(), merged)

        if self.debug:
            self.log.dbg('local variables resolved')
            self._debug_vars(merged)

        # resolve profile includes
        t = Templategen(variables=merged)
        for k, v in self.profiles.items():
            if self.key_profile_include in v:
                new = []
                for k in v[self.key_profile_include]:
                    new.append(t.generate_string(k))
                v[self.key_profile_include] = new

        # now get the included ones
        pro_var = self._get_included_variables(self.profile,
                                               seen=[self.profile])
        pro_dvar = self._get_included_dvariables(self.profile,
                                                 seen=[self.profile])
        # exec incl dynvariables
        self._shell_exec_dvars(pro_dvar.keys(), pro_dvar)

        # merge all and resolve
        merged = self._merge_dict(pro_var, merged)
        merged = self._merge_dict(pro_dvar, merged)
        merged = self._rec_resolve_vars(merged)

        if self.debug:
            self.log.dbg('resolve all uses of variables in config')
            self._debug_vars(merged)

        prokeys = list(pro_var.keys()) + list(pro_dvar.keys())
        return merged, prokeys

    def _apply_variables(self):
        """template any needed parts of the config"""
        t = Templategen(variables=self.variables)

        # dotfiles src/dst/actions keys
        for k, v in self.dotfiles.items():
            # src
            src = v.get(self.key_dotfile_src)
            v[self.key_dotfile_src] = t.generate_string(src)
            # dst
            dst = v.get(self.key_dotfile_dst)
            v[self.key_dotfile_dst] = t.generate_string(dst)

        # import_actions
        new = []
        entries = self.settings.get(self.key_import_actions, [])
        new = self._template_list(t, entries)
        if new:
            self.settings[self.key_import_actions] = new

        # import_configs
        entries = self.settings.get(self.key_import_configs, [])
        new = self._template_list(t, entries)
        if new:
            self.settings[self.key_import_configs] = new

        # import_variables
        entries = self.settings.get(self.key_import_variables, [])
        new = self._template_list(t, entries)
        if new:
            self.settings[self.key_import_variables] = new

        # profile's import
        for k, v in self.profiles.items():
            entries = v.get(self.key_import_profile_dfs, [])
            new = self._template_list(t, entries)
            if new:
                v[self.key_import_profile_dfs] = new

    def _norm_actions(self, actions):
        """
        ensure each action is either pre or post explicitely
        action entry of the form {action_key: (pre|post, action)}
        """
        if not actions:
            return actions
        new = {}
        for k, v in actions.items():
            if k == self.action_pre or k == self.action_post:
                for key, action in v.items():
                    new[key] = (k, action)
            else:
                new[k] = (self.action_post, v)
        return new

    def _norm_profiles(self, profiles):
        """normalize profiles entries"""
        if not profiles:
            return profiles
        new = {}
        for k, v in profiles.items():
            # add dotfiles entry if not present
            if self.key_profile_dotfiles not in v:
                v[self.key_profile_dotfiles] = []
            new[k] = v
        return new

    def _norm_dotfiles(self, dotfiles):
        """normalize dotfiles entries"""
        if not dotfiles:
            return dotfiles
        new = {}
        for k, v in dotfiles.items():
            # add 'src' as key' if not present
            if self.key_dotfile_src not in v:
                v[self.key_dotfile_src] = k
                new[k] = v
            else:
                new[k] = v
            # fix deprecated trans key
            if self.old_key_trans_r in v:
                msg = '\"trans\" is deprecated, please use \"trans_read\"'
                self.log.warn(msg)
                v[self.key_trans_r] = v[self.old_key_trans_r]
                del v[self.old_key_trans_r]
                new[k] = v
            # apply link value
            if self.key_dotfile_link not in v:
                val = self.settings[self.key_settings_link_dotfile_default]
                v[self.key_dotfile_link] = val
            # apply noempty if undefined
            if self.key_dotfile_noempty not in v:
                val = self.settings.get(self.key_settings_noempty, False)
                v[self.key_dotfile_noempty] = val
        return new

    def _get_variables_dict(self, profile):
        """return enriched variables"""
        variables = deepcopy(self.ori_variables)
        # add profile variable
        if profile:
            variables['profile'] = profile
        # add some more variables
        p = self.settings.get(self.key_settings_dotpath)
        p = self._norm_path(p)
        variables['_dotdrop_dotpath'] = p
        variables['_dotdrop_cfgpath'] = self._norm_path(self.path)
        p = self.settings.get(self.key_settings_workdir)
        p = self._norm_path(p)
        variables['_dotdrop_workdir'] = p
        return variables

    def _get_dvariables_dict(self):
        """return dynvariables"""
        variables = deepcopy(self.ori_dvariables)
        return variables

    def _get_included_variables(self, profile, seen):
        """return included variables"""
        variables = {}
        if not profile or profile not in self.profiles.keys():
            return variables

        # profile entry
        pentry = self.profiles.get(profile)

        # inherite profile variables
        for inherited_profile in pentry.get(self.key_profile_include, []):
            if inherited_profile == profile or inherited_profile in seen:
                raise YamlException('\"include\" loop')
            seen.append(inherited_profile)
            new = self._get_included_variables(inherited_profile,
                                               seen)
            if self.debug:
                msg = 'included vars from {}: {}'
                self.log.dbg(msg.format(inherited_profile, new))
            variables.update(new)

        cur = pentry.get(self.key_profile_variables, {})
        return self._merge_dict(cur, variables)

    def _get_included_dvariables(self, profile, seen):
        """return included dynvariables"""
        variables = {}

        if not profile or profile not in self.profiles.keys():
            return variables

        # profile entry
        pentry = self.profiles.get(profile)

        # inherite profile dynvariables
        for inherited_profile in pentry.get(self.key_profile_include, []):
            if inherited_profile == profile or inherited_profile in seen:
                raise YamlException('\"include loop\"')
            seen.append(inherited_profile)
            new = self._get_included_dvariables(inherited_profile, seen)
            if self.debug:
                msg = 'included dvars from {}: {}'
                self.log.dbg(msg.format(inherited_profile, new))
            variables.update(new)

        cur = pentry.get(self.key_profile_dvariables, {})
        return self._merge_dict(cur, variables)

    def _resolve_profile_all(self):
        """resolve some other parts of the config"""
        # profile -> ALL
        for k, v in self.profiles.items():
            dfs = v.get(self.key_profile_dotfiles, None)
            if not dfs:
                continue
            if self.key_all in dfs:
                if self.debug:
                    self.log.dbg('add ALL to profile {}'.format(k))
                v[self.key_profile_dotfiles] = self.dotfiles.keys()

    def _resolve_profile_includes(self):
        # profiles -> include other profile
        for k, v in self.profiles.items():
            self._rec_resolve_profile_include(k)

    def _rec_resolve_profile_include(self, profile):
        """
        recursively resolve include of other profiles's:
        * dotfiles
        * actions
        """
        this_profile = self.profiles[profile]

        # include
        dotfiles = this_profile.get(self.key_profile_dotfiles, [])
        actions = this_profile.get(self.key_profile_actions, [])
        includes = this_profile.get(self.key_profile_include, None)
        if not includes:
            # nothing to include
            return dotfiles, actions
        if self.debug:
            self.log.dbg('{} includes: {}'.format(profile, ','.join(includes)))
            self.log.dbg('{} dotfiles before include: {}'.format(profile,
                                                                 dotfiles))
            self.log.dbg('{} actions before include: {}'.format(profile,
                                                                actions))

        seen = []
        for i in uniq_list(includes):
            # ensure no include loop occurs
            if i in seen:
                raise YamlException('\"include loop\"')
            seen.append(i)
            # included profile even exists
            if i not in self.profiles.keys():
                self.log.warn('include unknown profile: {}'.format(i))
                continue
            # recursive resolve
            o_dfs, o_actions = self._rec_resolve_profile_include(i)
            # merge dotfile keys
            dotfiles.extend(o_dfs)
            this_profile[self.key_profile_dotfiles] = uniq_list(dotfiles)
            # merge actions keys
            actions.extend(o_actions)
            this_profile[self.key_profile_actions] = uniq_list(actions)

        dotfiles = this_profile.get(self.key_profile_dotfiles, [])
        actions = this_profile.get(self.key_profile_actions, [])
        if self.debug:
            self.log.dbg('{} dotfiles after include: {}'.format(profile,
                                                                dotfiles))
            self.log.dbg('{} actions after include: {}'.format(profile,
                                                               actions))

        # since dotfiles and actions are resolved here
        # and variables have been already done at the beginning
        # of the parsing, we can clear these include
        self.profiles[profile][self.key_profile_include] = None
        return dotfiles, actions

    ########################################################
    # handle imported entries
    ########################################################

    def _import_variables(self):
        """import external variables from paths"""
        paths = self.settings.get(self.key_import_variables, None)
        if not paths:
            return
        paths = self._glob_paths(paths)
        for p in paths:
            path = self._norm_path(p)
            if self.debug:
                self.log.dbg('import variables from {}'.format(path))
            var = self._import_sub(path, self.key_variables,
                                   mandatory=False)
            if self.debug:
                self.log.dbg('import dynvariables from {}'.format(path))
            dvar = self._import_sub(path, self.key_dvariables,
                                    mandatory=False)
            merged = self._merge_dict(dvar, var)
            merged = self._rec_resolve_vars(merged)
            # execute dvar
            self._shell_exec_dvars(dvar.keys(), merged)
            self._clear_profile_vars(merged)
            self.variables = self._merge_dict(merged, self.variables)

    def _clear_profile_vars(self, dic):
        """remove profile variables from dic if found"""
        [dic.pop(k, None) for k in self.prokeys]

    def _import_actions(self):
        """import external actions from paths"""
        paths = self.settings.get(self.key_import_actions, None)
        if not paths:
            return
        paths = self._glob_paths(paths)
        for p in paths:
            path = self._norm_path(p)
            if self.debug:
                self.log.dbg('import actions from {}'.format(path))
            new = self._import_sub(path, self.key_actions,
                                   mandatory=False,
                                   patch_func=self._norm_actions)
            self.actions = self._merge_dict(new, self.actions)

    def _import_profiles_dotfiles(self):
        """import profile dotfiles"""
        for k, v in self.profiles.items():
            imp = v.get(self.key_import_profile_dfs, None)
            if not imp:
                continue
            if self.debug:
                self.log.dbg('import dotfiles for profile {}'.format(k))
            paths = self._glob_paths(imp)
            for p in paths:
                current = v.get(self.key_dotfiles, [])
                path = self._norm_path(p)
                new = self._import_sub(path, self.key_dotfiles,
                                       mandatory=False)
                v[self.key_dotfiles] = new + current

    def _import_config(self, path):
        """import config from path"""
        path = self._norm_path(path)
        if self.debug:
            self.log.dbg('import config from {}'.format(path))
        sub = CfgYaml(path, profile=self.profile, debug=self.debug)
        # settings is ignored
        self.dotfiles = self._merge_dict(self.dotfiles, sub.dotfiles)
        self.profiles = self._merge_dict(self.profiles, sub.profiles)
        self.actions = self._merge_dict(self.actions, sub.actions)
        self.trans_r = self._merge_dict(self.trans_r, sub.trans_r)
        self.trans_w = self._merge_dict(self.trans_w, sub.trans_w)
        self._clear_profile_vars(sub.variables)
        if self.debug:
            self.log.dbg('add import_configs var: {}'.format(sub.variables))
        self.variables = self._merge_dict(sub.variables, self.variables)

    def _import_configs(self):
        """import configs from external files"""
        # settings -> import_configs
        imp = self.settings.get(self.key_import_configs, None)
        if not imp:
            return
        paths = self._glob_paths(imp)
        for path in paths:
            self._import_config(path)

    def _import_sub(self, path, key,
                    mandatory=False, patch_func=None):
        """
        import the block "key" from "path"
        patch_func is applied to each element if defined
        """
        if self.debug:
            self.log.dbg('import \"{}\" from \"{}\"'.format(key, path))
        extdict = self._load_yaml(path)
        new = self._get_entry(extdict, key, mandatory=mandatory)
        if patch_func:
            new = patch_func(new)
        if not new and mandatory:
            err = 'no \"{}\" imported from \"{}\"'.format(key, path)
            self.log.warn(err)
            raise YamlException(err)
        if self.debug:
            self.log.dbg('new \"{}\": {}'.format(key, new))
        return new

    ########################################################
    # add/remove entries
    ########################################################

    def _new_profile(self, key):
        """add a new profile if it doesn't exist"""
        if key not in self.profiles.keys():
            # update yaml_dict
            self.yaml_dict[self.key_profiles][key] = {
                self.key_profile_dotfiles: []
            }
            if self.debug:
                self.log.dbg('adding new profile: {}'.format(key))
            self.dirty = True

    def add_dotfile_to_profile(self, dotfile_key, profile_key):
        """add an existing dotfile key to a profile_key"""
        self._new_profile(profile_key)
        profile = self.yaml_dict[self.key_profiles][profile_key]
        if dotfile_key not in profile[self.key_profile_dotfiles]:
            profile[self.key_profile_dotfiles].append(dotfile_key)
            if self.debug:
                msg = 'add \"{}\" to profile \"{}\"'.format(dotfile_key,
                                                            profile_key)
                msg.format(dotfile_key, profile_key)
                self.log.dbg(msg)
            self.dirty = True
        return self.dirty

    def add_dotfile(self, key, src, dst, link):
        """add a new dotfile"""
        if key in self.dotfiles.keys():
            return False
        if self.debug:
            self.log.dbg('adding new dotfile: {}'.format(key))

        df_dict = {
            self.key_dotfile_src: src,
            self.key_dotfile_dst: dst,
        }
        dfl = self.settings[self.key_settings_link_dotfile_default]
        if str(link) != dfl:
            df_dict[self.key_dotfile_link] = str(link)
        self.yaml_dict[self.key_dotfiles][key] = df_dict
        self.dirty = True

    def del_dotfile(self, key):
        """remove this dotfile from config"""
        if key not in self.yaml_dict[self.key_dotfiles]:
            self.log.err('key not in dotfiles: {}'.format(key))
            return False
        if self.debug:
            self.log.dbg('remove dotfile: {}'.format(key))
        del self.yaml_dict[self.key_dotfiles][key]
        if self.debug:
            dfs = self.yaml_dict[self.key_dotfiles]
            self.log.dbg('new dotfiles: {}'.format(dfs))
        self.dirty = True
        return True

    def del_dotfile_from_profile(self, df_key, pro_key):
        """remove this dotfile from that profile"""
        if df_key not in self.dotfiles.keys():
            self.log.err('key not in dotfiles: {}'.format(df_key))
            return False
        if pro_key not in self.profiles.keys():
            self.log.err('key not in profile: {}'.format(pro_key))
            return False
        # get the profile dictionary
        profile = self.yaml_dict[self.key_profiles][pro_key]
        if df_key not in profile[self.key_profile_dotfiles]:
            return True
        if self.debug:
            dfs = profile[self.key_profile_dotfiles]
            self.log.dbg('{} profile dotfiles: {}'.format(pro_key, dfs))
            self.log.dbg('remove {} from profile {}'.format(df_key, pro_key))
        profile[self.key_profile_dotfiles].remove(df_key)
        if self.debug:
            dfs = profile[self.key_profile_dotfiles]
            self.log.dbg('{} profile dotfiles: {}'.format(pro_key, dfs))
        self.dirty = True
        return True

    ########################################################
    # handle deprecated entries
    ########################################################

    def _fix_deprecated(self, yamldict):
        """fix deprecated entries"""
        self._fix_deprecated_link_by_default(yamldict)
        self._fix_deprecated_dotfile_link(yamldict)

    def _fix_deprecated_link_by_default(self, yamldict):
        """fix deprecated link_by_default"""
        key = 'link_by_default'
        newkey = self.key_imp_link
        if self.key_settings not in yamldict:
            return
        if not yamldict[self.key_settings]:
            return
        config = yamldict[self.key_settings]
        if key not in config:
            return
        if config[key]:
            config[newkey] = self.lnk_link
        else:
            config[newkey] = self.lnk_nolink
        del config[key]
        self.log.warn('deprecated \"link_by_default\"')
        self.dirty = True

    def _fix_deprecated_dotfile_link(self, yamldict):
        """fix deprecated link in dotfiles"""
        if self.key_dotfiles not in yamldict:
            return
        if not yamldict[self.key_dotfiles]:
            return
        for k, dotfile in yamldict[self.key_dotfiles].items():
            new = self.lnk_nolink
            if self.key_dotfile_link in dotfile and \
                    type(dotfile[self.key_dotfile_link]) is bool:
                # patch link: <bool>
                cur = dotfile[self.key_dotfile_link]
                new = self.lnk_nolink
                if cur:
                    new = self.lnk_link
                dotfile[self.key_dotfile_link] = new
                self.dirty = True
                self.log.warn('deprecated \"link\" value')

            elif self.key_dotfile_link_children in dotfile and \
                    type(dotfile[self.key_dotfile_link_children]) is bool:
                # patch link_children: <bool>
                cur = dotfile[self.key_dotfile_link_children]
                new = self.lnk_nolink
                if cur:
                    new = self.lnk_children
                del dotfile[self.key_dotfile_link_children]
                dotfile[self.key_dotfile_link] = new
                self.dirty = True
                self.log.warn('deprecated \"link_children\" value')

    ########################################################
    # yaml utils
    ########################################################

    def save(self):
        """save this instance and return True if saved"""
        if not self.dirty:
            return False

        content = self._clear_none(self.dump())

        # make sure we have the base entries
        if self.key_settings not in content:
            content[self.key_settings] = None
        if self.key_dotfiles not in content:
            content[self.key_dotfiles] = None
        if self.key_profiles not in content:
            content[self.key_profiles] = None

        # save to file
        if self.debug:
            self.log.dbg('saving to {}'.format(self.path))
        try:
            self._yaml_dump(content, self.path)
        except Exception as e:
            self.log.err(e)
            raise YamlException('error saving config: {}'.format(self.path))

        self.dirty = False
        return True

    def dump(self):
        """dump the config dictionary"""
        return self.yaml_dict

    def _load_yaml(self, path):
        """load a yaml file to a dict"""
        content = {}
        if not os.path.exists(path):
            raise YamlException('config path not found: {}'.format(path))
        try:
            content = self._yaml_load(path)
        except Exception as e:
            self.log.err(e)
            raise YamlException('invalid config: {}'.format(path))
        return content

    def _yaml_load(self, path):
        """load from yaml"""
        with open(path, 'r') as f:
            y = yaml()
            y.typ = 'rt'
            content = y.load(f)
        return content

    def _yaml_dump(self, content, path):
        """dump to yaml"""
        with open(self.path, 'w') as f:
            y = yaml()
            y.default_flow_style = False
            y.indent = 2
            y.typ = 'rt'
            y.dump(content, f)

    ########################################################
    # helpers
    ########################################################

    def _merge_dict(self, high, low):
        """merge high and low dict"""
        if not high:
            high = {}
        if not low:
            low = {}
        return {**low, **high}

    def _get_entry(self, dic, key, mandatory=True):
        """return entry from yaml dictionary"""
        if key not in dic:
            if mandatory:
                raise YamlException('invalid config: no {} found'.format(key))
            dic[key] = {}
            return dic[key]
        if mandatory and not dic[key]:
            # ensure is not none
            dic[key] = {}
        return dic[key]

    def _clear_none(self, dic):
        """recursively delete all none/empty values in a dictionary."""
        new = {}
        for k, v in dic.items():
            newv = v
            if isinstance(v, dict):
                newv = self._clear_none(v)
                if not newv:
                    # no empty dict
                    continue
            if newv is None:
                # no None value
                continue
            if isinstance(newv, list) and not newv:
                # no empty list
                continue
            new[k] = newv
        return new

    def _is_glob(self, path):
        """quick test if path is a glob"""
        return '*' in path or '?' in path

    def _glob_paths(self, paths):
        """glob a list of paths"""
        if not isinstance(paths, list):
            paths = [paths]
        res = []
        for p in paths:
            if not self._is_glob(p):
                res.append(p)
                continue
            p = os.path.expanduser(p)
            new = glob.glob(p)
            if not new:
                raise YamlException('bad path: {}'.format(p))
            res.extend(glob.glob(p))
        return res

    def _debug_vars(self, variables):
        """pretty print variables"""
        if not self.debug:
            return
        self.log.dbg('variables:')
        for k, v in variables.items():
            self.log.dbg('\t\"{}\": {}'.format(k, v))

    def _norm_path(self, path):
        """resolve a path either absolute or relative to config path"""
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            d = os.path.dirname(self.path)
            return os.path.join(d, path)
        return os.path.normpath(path)

    def _shell_exec_dvars(self, keys, variables):
        """shell execute dynvariables"""
        for k in list(keys):
            ret, out = shell(variables[k], debug=self.debug)
            if not ret:
                err = 'var \"{}: {}\" failed: {}'.format(k, variables[k], out)
                self.log.err(err)
                raise YamlException(err)
            if self.debug:
                self.log.dbg('\"{}\": {} -> {}'.format(k, variables[k], out))
            variables[k] = out

    def _template_list(self, t, entries):
        """template a list of entries"""
        new = []
        if not entries:
            return new
        for e in entries:
            et = t.generate_string(e)
            if self.debug and e != et:
                self.log.dbg('resolved: {} -> {}'.format(e, et))
            new.append(et)
        return new
