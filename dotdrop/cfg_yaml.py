"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2019, deadc0de6

handle lower level of the config file

will provide the following dictionaries to
the upper layer:

* self.settings
* self.dotfiles
* self.profiles
* self.actions
* self.trans_r
* self.trans_w
* self.variables

Additionally a few methods are exported.
"""

# pylint: disable=C0302

import os
import glob
import io
from copy import deepcopy
from itertools import chain
from ruamel.yaml import YAML as yaml
import toml

# local imports
from dotdrop.version import __version__ as VERSION
from dotdrop.settings import Settings
from dotdrop.logger import Logger
from dotdrop.templategen import Templategen
from dotdrop.linktypes import LinkTypes
from dotdrop.utils import shellrun, uniq_list, userinput
from dotdrop.exceptions import YamlException, UndefinedException


class CfgYaml:
    """yaml config file parser"""

    # global entries
    key_settings = Settings.key_yaml
    key_dotfiles = 'dotfiles'
    key_profiles = 'profiles'
    key_actions = 'actions'
    old_key_trans_r = 'trans'
    key_trans_r = 'trans_read'
    key_trans_w = 'trans_write'
    key_variables = 'variables'
    key_dvariables = 'dynvariables'
    key_uvariables = 'uservariables'

    action_pre = 'pre'
    action_post = 'post'

    save_uservariables_name = 'uservariables{}.yaml'

    # profiles/dotfiles entries
    key_dotfile_src = 'src'
    key_dotfile_dst = 'dst'
    key_dotfile_link = 'link'
    key_dotfile_actions = 'actions'
    key_dotfile_noempty = 'ignoreempty'
    key_dotfile_template = 'template'
    key_dotfile_chmod = 'chmod'

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
    key_import_sep = ':'
    key_import_ignore_key = 'optional'
    key_import_fatal_not_found = True

    # settings
    key_settings_dotpath = Settings.key_dotpath
    key_settings_workdir = Settings.key_workdir
    key_settings_link_dotfile_default = Settings.key_link_dotfile_default
    key_settings_noempty = Settings.key_ignoreempty
    key_settings_minversion = Settings.key_minversion
    key_imp_link = Settings.key_link_on_import
    key_settings_template = Settings.key_template_dotfile_default

    # link values
    lnk_nolink = LinkTypes.NOLINK.name.lower()
    lnk_link = LinkTypes.LINK.name.lower()
    lnk_children = LinkTypes.LINK_CHILDREN.name.lower()
    lnk_absolute = LinkTypes.ABSOLUTE.name.lower()
    lnk_relative = LinkTypes.RELATIVE.name.lower()

    # checks
    allowed_link_val = [lnk_nolink, lnk_link, lnk_children,
                        lnk_absolute, lnk_relative]
    top_entries = [key_dotfiles, key_settings, key_profiles]

    def __init__(self, path, profile=None, addprofiles=None,
                 reloading=False, debug=False, imported_configs=None):
        """
        config parser
        @path: config file path
        @profile: the selected profile names
        @addprofiles: included profiles names (list)
        @reloading: true when reloading
        @imported_configs: paths of config files that have been imported so far
        @debug: debug flag
        """
        self._path = os.path.abspath(path)
        self._profile = profile
        self._reloading = reloading
        self._debug = debug
        self._log = Logger(debug=self._debug)
        # config format
        self._config_format = 'yaml'
        # config needs to be written
        self._dirty = False
        # indicates the config has been updated
        self._dirty_deprecated = False
        # profile variables
        self._profilevarskeys = []
        # included profiles
        self._inc_profiles = addprofiles or []
        # imported configs
        self.imported_configs = imported_configs or []

        # init the dictionaries
        self.settings = {}
        self.dotfiles = {}
        self.profiles = {}
        self.actions = {}
        self.trans_r = {}
        self.trans_w = {}
        self.variables = {}

        if not os.path.exists(self._path):
            err = 'invalid config path: \"{}\"'.format(path)
            if self._debug:
                self._dbg(err)
            raise YamlException(err)

        self._dbg('START of config parsing')
        self._dbg('reloading: {}'.format(reloading))
        self._dbg('profile: {}'.format(profile))
        self._dbg('included profiles: {}'.format(','.join(self._inc_profiles)))

        self._yaml_dict = self._load_yaml(self._path)
        # live patch deprecated entries
        self._fix_deprecated(self._yaml_dict)
        # validate content
        self._validate(self._yaml_dict)

        ##################################################
        # parse the config and variables
        ##################################################

        # parse the "config" block
        self.settings = self._parse_blk_settings(self._yaml_dict)

        # base templater (when no vars/dvars exist)
        self.variables = self._enrich_vars(self.variables, self._profile)
        self._redefine_templater()

        # variables and dynvariables need to be first merged
        # before being templated in order to allow cyclic
        # references between them

        # parse the "variables" block
        var = self._parse_blk_variables(self._yaml_dict)
        self._add_variables(var, template=False)

        # parse the "dynvariables" block
        dvariables = self._parse_blk_dynvariables(self._yaml_dict)
        self._add_variables(dvariables, template=False)

        # now template variables and dynvariables from the same pool
        self._rec_resolve_variables(self.variables)
        # and execute dvariables
        # since this is done after recursively resolving variables
        # and dynvariables this means that variables referencing
        # dynvariables will result with the not executed value
        if dvariables.keys():
            self._shell_exec_dvars(self.variables, keys=dvariables.keys())
        # finally redefine the template
        self._redefine_templater()

        if self._debug:
            title = 'current variables defined'
            self._debug_dict(title, self.variables)

        # parse the "profiles" block
        self.profiles = self._parse_blk_profiles(self._yaml_dict)

        # include the profile's variables/dynvariables last
        # as it overwrites existing ones
        incpro, pvar, pdvar = self._get_profile_included_vars()
        self._inc_profiles = uniq_list(self._inc_profiles + incpro)
        self._add_variables(pvar, prio=True)
        self._add_variables(pdvar, shell=True, prio=True)
        self._profilevarskeys.extend(pvar.keys())
        self._profilevarskeys.extend(pdvar.keys())

        # template variables
        self.variables = self._template_dict(self.variables)
        if self._debug:
            title = 'variables defined (after template dict)'
            self._debug_dict(title, self.variables)

        ##################################################
        # template the "include" entries
        ##################################################

        self._template_include_entry()
        if self._debug:
            title = 'variables defined (after template include)'
            self._debug_dict(title, self.variables)

        ##################################################
        # template config entries
        ##################################################
        entry = self.settings[self.key_settings_dotpath]
        val = self._template_item(entry)
        self.settings[self.key_settings_dotpath] = val

        ##################################################
        # parse the other blocks
        ##################################################

        # parse the "dotfiles" block
        self.dotfiles = self._parse_blk_dotfiles(self._yaml_dict)
        # parse the "actions" block
        self.actions = self._parse_blk_actions(self._yaml_dict)
        # parse the "trans_r" block
        self.trans_r = self._parse_blk_trans_r(self._yaml_dict)
        # parse the "trans_w" block
        self.trans_w = self._parse_blk_trans_w(self._yaml_dict)

        ##################################################
        # import elements
        ##################################################

        # process imported variables (import_variables)
        newvars = self._import_variables()
        self._clear_profile_vars(newvars)
        self._add_variables(newvars)

        # process imported actions (import_actions)
        self._import_actions()
        # process imported profile dotfiles (import)
        self._import_profiles_dotfiles()
        # process imported configs (import_configs)
        self._import_configs()

        # process profile include
        self._resolve_profile_includes()

        # add the current profile variables
        _, pvar, pdvar = self._get_profile_included_vars()
        self._add_variables(pvar, prio=False)
        self._add_variables(pdvar, shell=True, prio=False)
        self._profilevarskeys.extend(pvar.keys())
        self._profilevarskeys.extend(pdvar.keys())

        # resolve variables
        self._clear_profile_vars(newvars)
        self._add_variables(newvars)

        # process profile ALL
        self._resolve_profile_all()
        # template dotfiles entries
        self._template_dotfiles_entries()

        # parse the "uservariables" block
        uvariables = self._parse_blk_uservariables(self._yaml_dict,
                                                   self.variables)
        self._add_variables(uvariables, template=False, prio=False)

        # end of parsing
        if self._debug:
            self._dbg('########### {} ###########'.format('final config'))
            self._debug_entries()
            self._dbg('END of config parsing')

    ########################################################
    # public methods
    ########################################################

    def _resolve_dotfile_link(self, link):
        """resolve dotfile link entry"""
        newlink = self._template_item(link)
        # check link value
        if newlink not in self.allowed_link_val:
            err = 'bad link value: {}'.format(newlink)
            self._log.err(err)
            self._log.err('allowed: {}'.format(self.allowed_link_val))
            raise YamlException('config content error: {}'.format(err))
        return newlink

    def resolve_dotfile_src(self, src, templater=None):
        """resolve dotfile src path"""
        newsrc = ''
        if src:
            new = src
            if templater:
                new = templater.generate_string(src)
            if new != src and self._debug:
                msg = 'dotfile src: \"{}\" -> \"{}\"'.format(src, new)
                self._dbg(msg)
            src = new
            src = os.path.join(self.settings[self.key_settings_dotpath],
                               src)
            newsrc = self._norm_path(src)
        return newsrc

    def resolve_dotfile_dst(self, dst, templater=None):
        """resolve dotfile dst path"""
        newdst = ''
        if dst:
            new = dst
            if templater:
                new = templater.generate_string(dst)
            if new != dst and self._debug:
                msg = 'dotfile dst: \"{}\" -> \"{}\"'.format(dst, new)
                self._dbg(msg)
            dst = new
            newdst = self._norm_path(dst)
        return newdst

    def add_dotfile_to_profile(self, dotfile_key, profile_key):
        """
        add an existing dotfile key to a profile_key
        we test using profiles variable since it merges
        imported ones (include, etc) but insert in main
        yaml only
        """
        # create the profile if it doesn't exist
        self._new_profile(profile_key)
        profile = self.profiles[profile_key]

        # ensure profile dotfiles list is not None
        if self.key_profile_dotfiles not in profile or \
                profile[self.key_profile_dotfiles] is None:
            profile[self.key_profile_dotfiles] = []
            self._yaml_dict[self.key_profiles][profile_key] = []

        # add to the profile
        pdfs = profile[self.key_profile_dotfiles]
        if self.key_all not in pdfs and \
                dotfile_key not in pdfs:
            # append dotfile
            pro = self._yaml_dict[self.key_profiles][profile_key]
            pro[self.key_profile_dotfiles].append(dotfile_key)
            if self._debug:
                msg = 'add \"{}\" to profile \"{}\"'.format(dotfile_key,
                                                            profile_key)
                msg.format(dotfile_key, profile_key)
                self._dbg(msg)
            self._dirty = True
        return self._dirty

    def get_all_dotfile_keys(self):
        """return all existing dotfile keys"""
        return self.dotfiles.keys()

    def update_dotfile(self, key, chmod):
        """update an existing dotfile"""
        if key not in self.dotfiles.keys():
            return False
        dotfile = self._yaml_dict[self.key_dotfiles][key]
        old = None
        if self.key_dotfile_chmod in dotfile:
            old = dotfile[self.key_dotfile_chmod]
        if old == chmod:
            return False
        if self._debug:
            self._dbg('update dotfile: {}'.format(key))
            self._dbg('old chmod value: {}'.format(old))
            self._dbg('new chmod value: {}'.format(chmod))
        dotfile = self._yaml_dict[self.key_dotfiles][key]
        if not chmod:
            del dotfile[self.key_dotfile_chmod]
        else:
            dotfile[self.key_dotfile_chmod] = str(format(chmod, 'o'))
        self._dirty = True
        return True

    def add_dotfile(self, key, src, dst, link, chmod=None,
                    trans_r_key=None, trans_w_key=None):
        """add a new dotfile"""
        if key in self.dotfiles.keys():
            return False
        if self._debug:
            self._dbg('adding new dotfile: {}'.format(key))
            self._dbg('new dotfile src: {}'.format(src))
            self._dbg('new dotfile dst: {}'.format(dst))
            self._dbg('new dotfile link: {}'.format(link))
            self._dbg('new dotfile chmod: {}'.format(chmod))
            self._dbg('new dotfile trans_r: {}'.format(trans_r_key))
            self._dbg('new dotfile trans_w: {}'.format(trans_w_key))

        # create the dotfile dict
        df_dict = {
            self.key_dotfile_src: src,
            self.key_dotfile_dst: dst,
        }

        # link
        dfl = self.settings[self.key_settings_link_dotfile_default]
        if str(link) != dfl:
            df_dict[self.key_dotfile_link] = str(link)

        # chmod
        if chmod:
            df_dict[self.key_dotfile_chmod] = str(format(chmod, 'o'))

        # trans_r/trans_w
        if trans_r_key:
            df_dict[self.key_trans_r] = str(trans_r_key)
        if trans_w_key:
            df_dict[self.key_trans_w] = str(trans_w_key)

        if self._debug:
            self._dbg('dotfile dict: {}'.format(df_dict))

        # add to global dict
        self._yaml_dict[self.key_dotfiles][key] = df_dict
        self._dirty = True
        return True

    def del_dotfile(self, key):
        """remove this dotfile from config"""
        if key not in self._yaml_dict[self.key_dotfiles]:
            self._log.err('key not in dotfiles: {}'.format(key))
            return False
        if self._debug:
            self._dbg('remove dotfile: {}'.format(key))
        del self._yaml_dict[self.key_dotfiles][key]
        if self._debug:
            dfs = self._yaml_dict[self.key_dotfiles]
            self._dbg('new dotfiles: {}'.format(dfs))
        self._dirty = True
        return True

    def del_dotfile_from_profile(self, df_key, pro_key):
        """remove this dotfile from that profile"""
        if self._debug:
            self._dbg('removing \"{}\" from \"{}\"'.format(df_key, pro_key))
        if df_key not in self.dotfiles.keys():
            self._log.err('key not in dotfiles: {}'.format(df_key))
            return False
        if pro_key not in self.profiles.keys():
            self._log.err('key not in profile: {}'.format(pro_key))
            return False
        # get the profile dictionary
        profile = self._yaml_dict[self.key_profiles][pro_key]
        if self.key_profile_dotfiles not in profile:
            # profile does not contain any dotfiles
            return True
        if df_key not in profile[self.key_profile_dotfiles]:
            return True
        if self._debug:
            dfs = profile[self.key_profile_dotfiles]
            self._dbg('{} profile dotfiles: {}'.format(pro_key, dfs))
            self._dbg('remove {} from profile {}'.format(df_key, pro_key))
        profile[self.key_profile_dotfiles].remove(df_key)
        if self._debug:
            dfs = profile[self.key_profile_dotfiles]
            self._dbg('{} profile dotfiles: {}'.format(pro_key, dfs))
        self._dirty = True
        return True

    def save(self):
        """save this instance and return True if saved"""
        if not self._dirty:
            return False

        content = self._prepare_to_save(self._yaml_dict)

        if self._dirty_deprecated:
            # add minversion
            settings = content[self.key_settings]
            settings[self.key_settings_minversion] = VERSION

        # save to file
        if self._debug:
            self._dbg('saving to {}'.format(self._path))
        try:
            with open(self._path, 'w', encoding='utf8') as file:
                self._yaml_dump(content, file, fmt=self._config_format)
        except Exception as exc:
            self._log.err(exc)
            err = 'error saving config: {}'.format(self._path)
            raise YamlException(err) from exc

        if self._dirty_deprecated:
            warn = 'your config contained deprecated entries'
            warn += ' and was updated'
            self._log.warn(warn)

        self._dirty = False
        return True

    def dump(self):
        """dump the config dictionary"""
        output = io.StringIO()
        content = self._prepare_to_save(self._yaml_dict.copy())
        self._yaml_dump(content, output, fmt=self._config_format)
        return output.getvalue()

    ########################################################
    # block parsing
    ########################################################

    def _parse_blk_settings(self, dic):
        """parse the "config" block"""
        block = self._get_entry(dic, self.key_settings).copy()
        # set defaults
        settings = Settings(None).serialize().get(self.key_settings)
        settings.update(block)

        # resolve minimum version
        if self.key_settings_minversion in settings:
            minversion = settings[self.key_settings_minversion]
            self._check_minversion(minversion)

        # normalize paths
        paths = self._norm_path(settings[self.key_settings_dotpath])
        settings[self.key_settings_dotpath] = paths
        paths = self._norm_path(settings[self.key_settings_workdir])
        settings[self.key_settings_workdir] = paths
        paths = [
            self._norm_path(path)
            for path in settings[Settings.key_filter_file]
        ]
        settings[Settings.key_filter_file] = paths
        paths = [
            self._norm_path(path)
            for path in settings[Settings.key_func_file]
        ]
        settings[Settings.key_func_file] = paths
        if self._debug:
            self._debug_dict('settings block:', settings)
        return settings

    def _parse_blk_dotfiles(self, dic):
        """parse the "dotfiles" block"""
        dotfiles = self._get_entry(dic, self.key_dotfiles).copy()
        keys = dotfiles.keys()
        if len(keys) != len(list(set(keys))):
            dups = [x for x in keys if x not in list(set(keys))]
            err = 'duplicate dotfile keys found: {}'.format(dups)
            raise YamlException(err)

        dotfiles = self._norm_dotfiles(dotfiles)
        if self._debug:
            self._debug_dict('dotfiles block', dotfiles)
        return dotfiles

    def _parse_blk_profiles(self, dic):
        """parse the "profiles" block"""
        profiles = self._get_entry(dic, self.key_profiles).copy()
        profiles = self._norm_profiles(profiles)
        if self._debug:
            self._debug_dict('profiles block', profiles)
        return profiles

    def _parse_blk_actions(self, dic):
        """parse the "actions" block"""
        actions = self._get_entry(dic, self.key_actions,
                                  mandatory=False)
        if actions:
            actions = actions.copy()
        actions = self._norm_actions(actions)
        if self._debug:
            self._debug_dict('actions block', actions)
        return actions

    def _parse_blk_trans_r(self, dic):
        """parse the "trans_r" block"""
        key = self.key_trans_r
        if self.old_key_trans_r in dic:
            msg = '\"trans\" is deprecated, please use \"trans_read\"'
            self._log.warn(msg)
            dic[self.key_trans_r] = dic[self.old_key_trans_r]
            del dic[self.old_key_trans_r]
        trans_r = self._get_entry(dic, key, mandatory=False)
        if trans_r:
            trans_r = trans_r.copy()
        if self._debug:
            self._debug_dict('trans_r block', trans_r)
        return trans_r

    def _parse_blk_trans_w(self, dic):
        """parse the "trans_w" block"""
        trans_w = self._get_entry(dic, self.key_trans_w,
                                  mandatory=False)
        if trans_w:
            trans_w = trans_w.copy()
        if self._debug:
            self._debug_dict('trans_w block', trans_w)
        return trans_w

    def _parse_blk_variables(self, dic):
        """parse the "variables" block"""
        variables = self._get_entry(dic,
                                    self.key_variables,
                                    mandatory=False)
        if variables:
            variables = variables.copy()
        if self._debug:
            self._debug_dict('variables block', variables)
        return variables

    def _parse_blk_dynvariables(self, dic):
        """parse the "dynvariables" block"""
        dvariables = self._get_entry(dic,
                                     self.key_dvariables,
                                     mandatory=False)
        if dvariables:
            dvariables = dvariables.copy()
        if self._debug:
            self._debug_dict('dynvariables block', dvariables)
        return dvariables

    def _parse_blk_uservariables(self, dic, current):
        """parse the "uservariables" block"""
        uvariables = self._get_entry(dic,
                                     self.key_uvariables,
                                     mandatory=False)

        uvars = {}
        if not self._reloading and uvariables:
            try:
                for name, prompt in uvariables.items():
                    if name in current:
                        # ignore if already defined
                        if self._debug:
                            self._dbg('ignore uservariables {}'.format(name))
                        continue
                    content = userinput(prompt, debug=self._debug)
                    uvars[name] = content
            except KeyboardInterrupt as exc:
                raise YamlException('interrupted') from exc

            if uvars:
                uvars = uvars.copy()
        if self._debug:
            self._debug_dict('uservariables block', uvars)

        # save uservariables
        if uvars:
            try:
                self._save_uservariables(uvars)
            except YamlException:
                # ignore
                pass

        return uvars

    ########################################################
    # parsing helpers
    ########################################################
    def _template_include_entry(self):
        """template all "include" entries"""
        # import_actions
        new = []
        entries = self.settings.get(self.key_import_actions, [])
        new = self._template_list(entries)
        if new:
            self.settings[self.key_import_actions] = new

        # import_configs
        entries = self.settings.get(self.key_import_configs, [])
        new = self._template_list(entries)
        if new:
            self.settings[self.key_import_configs] = new

        # import_variables
        entries = self.settings.get(self.key_import_variables, [])
        new = self._template_list(entries)
        if new:
            self.settings[self.key_import_variables] = new

        # profile's import
        for _, val in self.profiles.items():
            entries = val.get(self.key_import_profile_dfs, [])
            new = self._template_list(entries)
            if new:
                val[self.key_import_profile_dfs] = new

    def _norm_actions(self, actions):
        """
        ensure each action is either pre or post explicitely
        action entry of the form {action_key: (pre|post, action)}
        """
        if not actions:
            return actions
        new = {}
        for k, val in actions.items():
            if k in (self.action_pre, self.action_post):
                for key, action in val.items():
                    new[key] = (k, action)
            else:
                new[k] = (self.action_post, val)
        return new

    def _norm_profiles(self, profiles):
        """normalize profiles entries"""
        if not profiles:
            return profiles
        new = {}
        for k, val in profiles.items():
            if not val:
                # no dotfiles
                continue
            # add dotfiles entry if not present
            if self.key_profile_dotfiles not in val:
                val[self.key_profile_dotfiles] = []
            new[k] = val
        return new

    def _norm_dotfiles(self, dotfiles):
        """normalize and check dotfiles entries"""
        if not dotfiles:
            return dotfiles
        new = {}
        for k, val in dotfiles.items():
            # add 'src' as key' if not present
            if self.key_dotfile_src not in val:
                val[self.key_dotfile_src] = k
                new[k] = val
            else:
                new[k] = val
            # fix deprecated trans key
            if self.old_key_trans_r in val:
                msg = '\"trans\" is deprecated, please use \"trans_read\"'
                self._log.warn(msg)
                val[self.key_trans_r] = val[self.old_key_trans_r]
                del val[self.old_key_trans_r]
                new[k] = val
            if self.key_dotfile_link not in val:
                # apply link value if undefined
                value = self.settings[self.key_settings_link_dotfile_default]
                val[self.key_dotfile_link] = value
            # apply noempty if undefined
            if self.key_dotfile_noempty not in val:
                value = self.settings.get(self.key_settings_noempty, False)
                val[self.key_dotfile_noempty] = value
            # apply template if undefined
            if self.key_dotfile_template not in val:
                value = self.settings.get(self.key_settings_template, True)
                val[self.key_dotfile_template] = value
            # validate value of chmod if defined
            if self.key_dotfile_chmod in val:
                value = str(val[self.key_dotfile_chmod])
                if len(value) < 3:
                    err = 'bad format for chmod: {}'.format(value)
                    self._log.err(err)
                    raise YamlException('config content error: {}'.format(err))
                try:
                    int(value)
                except Exception as exc:
                    err = 'bad format for chmod: {}'.format(value)
                    self._log.err(err)
                    err = 'config content error: {}'.format(err)
                    raise YamlException(err) from exc
                # normalize chmod value
                for chmodv in list(value):
                    chmodint = int(chmodv)
                    if chmodint < 0 or chmodint > 7:
                        err = 'bad format for chmod: {}'.format(value)
                        self._log.err(err)
                        raise YamlException(
                            'config content error: {}'.format(err)
                        )
                val[self.key_dotfile_chmod] = int(value, 8)

        return new

    def _add_variables(self, new, shell=False, template=True, prio=False):
        """
        add new variables
        @shell: execute the variable through the shell
        @template: template the variable
        @prio: new takes priority over existing variables
        """
        if not new:
            return
        # merge
        if prio:
            self.variables = self._merge_dict(new, self.variables)
        else:
            # clear existing variable
            for k in list(new.keys()):
                if k in self.variables.keys():
                    del new[k]
            # merge
            self.variables = self._merge_dict(self.variables, new)
        # ensure enriched variables are relative to this config
        self.variables = self._enrich_vars(self.variables, self._profile)
        # re-create the templater
        self._redefine_templater()
        if template:
            # rec resolve variables with new ones
            self._rec_resolve_variables(self.variables)
        if shell and new:
            # shell exec
            self._shell_exec_dvars(self.variables, keys=new.keys())
            # re-create the templater
            self._redefine_templater()

    def _enrich_vars(self, variables, profile):
        """return enriched variables"""
        # add profile variable
        if profile:
            variables['profile'] = profile
        # add some more variables
        path = self.settings.get(self.key_settings_dotpath)
        path = self._norm_path(path)
        variables['_dotdrop_dotpath'] = path
        variables['_dotdrop_cfgpath'] = self._norm_path(self._path)
        path = self.settings.get(self.key_settings_workdir)
        path = self._norm_path(path)
        variables['_dotdrop_workdir'] = path
        return variables

    def _get_profile_included_item(self, keyitem):
        """recursively get included <keyitem> in profile"""
        profiles = [self._profile] + self._inc_profiles
        items = {}
        for profile in profiles:
            seen = [self._profile]
            i = self.__get_profile_included_item(profile, keyitem, seen)
            items = self._merge_dict(i, items)
        return items

    def __get_profile_included_item(self, profile, keyitem, seen):
        """recursively get included <keyitem> from profile"""
        items = {}
        if not profile or profile not in self.profiles.keys():
            return items

        # considered profile entry
        pentry = self.profiles.get(profile)

        # recursively get <keyitem> from inherited profile
        for inherited_profile in pentry.get(self.key_profile_include, []):
            if inherited_profile == profile or inherited_profile in seen:
                raise YamlException('\"include\" loop')
            seen.append(inherited_profile)
            new = self.__get_profile_included_item(inherited_profile,
                                                   keyitem, seen)
            if self._debug:
                msg = 'included {} from {}: {}'
                self._dbg(msg.format(keyitem, inherited_profile, new))
            items.update(new)

        cur = pentry.get(keyitem, {})
        return self._merge_dict(cur, items)

    def _resolve_profile_all(self):
        """resolve some other parts of the config"""
        # profile -> ALL
        for k, val in self.profiles.items():
            dfs = val.get(self.key_profile_dotfiles, None)
            if not dfs:
                continue
            if self.key_all in dfs:
                if self._debug:
                    self._dbg('add ALL to profile \"{}\"'.format(k))
                val[self.key_profile_dotfiles] = self.dotfiles.keys()

    def _resolve_profile_includes(self):
        """resolve profile(s) including other profiles"""
        for k, _ in self.profiles.items():
            self._rec_resolve_profile_include(k)

    def _rec_resolve_profile_include(self, profile):
        """
        recursively resolve include of other profiles's:
        * dotfiles
        * actions
        returns dotfiles, actions
        """
        this_profile = self.profiles[profile]

        # considered profile content
        dotfiles = this_profile.get(self.key_profile_dotfiles, []) or []
        actions = this_profile.get(self.key_profile_actions, []) or []
        includes = this_profile.get(self.key_profile_include, []) or []
        if not includes:
            # nothing to include
            return dotfiles, actions

        if self._debug:
            self._dbg('{} includes {}'.format(profile, ','.join(includes)))
            self._dbg('{} dotfiles before include: {}'.format(profile,
                                                              dotfiles))
            self._dbg('{} actions before include: {}'.format(profile,
                                                             actions))

        seen = []
        for i in uniq_list(includes):
            if self._debug:
                self._dbg('resolving includes "{}" <- "{}"'
                          .format(profile, i))

            # ensure no include loop occurs
            if i in seen:
                raise YamlException('\"include loop\"')
            seen.append(i)
            # included profile even exists
            if i not in self.profiles.keys():
                self._log.warn('include unknown profile: {}'.format(i))
                continue

            # recursive resolve
            if self._debug:
                self._dbg('recursively resolving includes for profile "{}"'
                          .format(i))
            o_dfs, o_actions = self._rec_resolve_profile_include(i)

            # merge dotfile keys
            if self._debug:
                self._dbg('Merging dotfiles {} <- {}: {} <- {}'
                          .format(profile, i, dotfiles, o_dfs))
            dotfiles.extend(o_dfs)
            this_profile[self.key_profile_dotfiles] = uniq_list(dotfiles)

            # merge actions keys
            if self._debug:
                self._dbg('Merging actions {} <- {}: {} <- {}'
                          .format(profile, i, actions, o_actions))
            actions.extend(o_actions)
            this_profile[self.key_profile_actions] = uniq_list(actions)

        dotfiles = this_profile.get(self.key_profile_dotfiles, [])
        actions = this_profile.get(self.key_profile_actions, [])

        if self._debug:
            self._dbg('{} dotfiles after include: {}'.format(profile,
                                                             dotfiles))
            self._dbg('{} actions after include: {}'.format(profile,
                                                            actions))

        # since included items are resolved here
        # we can clear these include
        self.profiles[profile][self.key_profile_include] = []
        return dotfiles, actions

    ########################################################
    # handle imported entries
    ########################################################

    def _import_variables(self):
        """import external variables from paths"""
        paths = self.settings.get(self.key_import_variables, None)
        if not paths:
            return None
        paths = self._resolve_paths(paths)
        newvars = {}
        for path in paths:
            if self._debug:
                self._dbg('import variables from {}'.format(path))
            var = self._import_sub(path, self.key_variables,
                                   mandatory=False)
            if self._debug:
                self._dbg('import dynvariables from {}'.format(path))
            dvar = self._import_sub(path, self.key_dvariables,
                                    mandatory=False)

            merged = self._merge_dict(dvar, var)
            self._rec_resolve_variables(merged)
            if dvar.keys():
                self._shell_exec_dvars(merged, keys=dvar.keys())
            self._clear_profile_vars(merged)
            newvars = self._merge_dict(newvars, merged)
        if self._debug:
            self._debug_dict('imported variables', newvars)
        return newvars

    def _import_actions(self):
        """import external actions from paths"""
        paths = self.settings.get(self.key_import_actions, None)
        if not paths:
            return
        paths = self._resolve_paths(paths)
        for path in paths:
            if self._debug:
                self._dbg('import actions from {}'.format(path))
            new = self._import_sub(path, self.key_actions,
                                   mandatory=False,
                                   patch_func=self._norm_actions)
            self.actions = self._merge_dict(new, self.actions)

    def _import_profiles_dotfiles(self):
        """import profile dotfiles"""
        for k, val in self.profiles.items():
            imp = val.get(self.key_import_profile_dfs, None)
            if not imp:
                continue
            if self._debug:
                self._dbg('import dotfiles for profile {}'.format(k))
            paths = self._resolve_paths(imp)
            for path in paths:
                current = val.get(self.key_dotfiles, [])
                new = self._import_sub(path, self.key_dotfiles,
                                       mandatory=False)
                val[self.key_dotfiles] = new + current

    def _import_config(self, path):
        """import config from path"""
        if self._debug:
            self._dbg('import config from {}'.format(path))
            self._dbg('profile: {}'.format(self._profile))
            self._dbg('included profiles: {}'.format(self._inc_profiles))
        sub = CfgYaml(path, profile=self._profile,
                      addprofiles=self._inc_profiles,
                      debug=self._debug,
                      imported_configs=self.imported_configs)

        # settings are ignored from external file
        # except for filter_file and func_file
        self.settings[Settings.key_func_file] += [
            self._norm_path(func_file)
            for func_file in sub.settings[Settings.key_func_file]
        ]
        self.settings[Settings.key_filter_file] += [
            self._norm_path(func_file)
            for func_file in sub.settings[Settings.key_filter_file]
        ]

        # merge top entries
        self.dotfiles = self._merge_dict(self.dotfiles, sub.dotfiles)
        self.profiles = self._merge_dict(self.profiles, sub.profiles,
                                         deep=True)
        self.actions = self._merge_dict(self.actions, sub.actions)
        self.trans_r = self._merge_dict(self.trans_r, sub.trans_r)
        self.trans_w = self._merge_dict(self.trans_w, sub.trans_w)
        self._clear_profile_vars(sub.variables)

        self.imported_configs.append(path)
        self.imported_configs += sub.imported_configs

        if self._debug:
            self._debug_dict('add import_configs var', sub.variables)
        self._add_variables(sub.variables, prio=True)

    def _import_configs(self):
        """import configs from external files"""
        # settings -> import_configs
        imp = self.settings.get(self.key_import_configs, None)
        if not imp:
            return
        paths = self._resolve_paths(imp)
        for path in paths:
            if path in self.imported_configs:
                err = '{} imported more than once in {}'.format(path,
                                                                self._path)
                raise YamlException(err)
            self._import_config(path)

    def _import_sub(self, path, key, mandatory=False, patch_func=None):
        """
        import the block "key" from "path"
        patch_func is applied to each element if defined
        """
        if self._debug:
            self._dbg('import \"{}\" from \"{}\"'.format(key, path))
        extdict = self._load_yaml(path)
        new = self._get_entry(extdict, key, mandatory=mandatory)
        if patch_func:
            if self._debug:
                self._dbg('calling patch: {}'.format(patch_func))
            new = patch_func(new)
        if not new and mandatory:
            err = 'no \"{}\" imported from \"{}\"'.format(key, path)
            self._log.warn(err)
            raise YamlException(err)
        if self._debug:
            self._dbg('imported \"{}\": {}'.format(key, new))
        return new

    ########################################################
    # add/remove entries
    ########################################################

    def _new_profile(self, key):
        """add a new profile if it doesn't exist"""
        if key not in self.profiles.keys():
            # update yaml_dict
            self._yaml_dict[self.key_profiles][key] = {
                self.key_profile_dotfiles: []
            }
            self.profiles[key] = {
                self.key_profile_dotfiles: []
            }
            if self._debug:
                self._dbg('adding new profile: {}'.format(key))
            self._dirty = True

    ########################################################
    # handle deprecated entries
    ########################################################

    def _fix_deprecated(self, yamldict):
        """fix deprecated entries"""
        if not yamldict:
            return
        self._fix_deprecated_link_by_default(yamldict)
        self._fix_deprecated_dotfile_link(yamldict)

    def _fix_deprecated_link_by_default(self, yamldict):
        """fix deprecated link_by_default"""
        old_key = 'link_by_default'
        newkey = self.key_imp_link
        if self.key_settings not in yamldict:
            return
        if not yamldict[self.key_settings]:
            return
        config = yamldict[self.key_settings]
        if old_key not in config:
            return
        if config[old_key]:
            config[newkey] = self.lnk_link
        else:
            config[newkey] = self.lnk_nolink
        del config[old_key]
        self._log.warn('deprecated \"link_by_default\"')
        self._dirty = True
        self._dirty_deprecated = True

    def _fix_deprecated_dotfile_link(self, yamldict):
        """fix deprecated link in dotfiles"""
        old_key = 'link_children'
        if self.key_dotfiles not in yamldict:
            return
        if not yamldict[self.key_dotfiles]:
            return
        for _, dotfile in yamldict[self.key_dotfiles].items():
            if self.key_dotfile_link in dotfile and \
                    isinstance(dotfile[self.key_dotfile_link], bool):
                # patch link: <bool>
                cur = dotfile[self.key_dotfile_link]
                new = self.lnk_nolink
                if cur:
                    new = self.lnk_link
                dotfile[self.key_dotfile_link] = new
                self._dirty = True
                self._dirty_deprecated = True
                warn = 'deprecated \"link: <boolean>\"'
                warn += ', updated to \"link: {}\"'.format(new)
                self._log.warn(warn)

            if self.key_dotfile_link in dotfile and \
                    dotfile[self.key_dotfile_link] == self.lnk_link:
                # patch "link: link"
                # to "link: absolute"
                new = self.lnk_absolute
                dotfile[self.key_dotfile_link] = new
                self._dirty = True
                self._dirty_deprecated = True
                warn = 'deprecated \"link: link\"'
                warn += ', updated to \"link: {}\"'.format(new)
                self._log.warn(warn)

            if old_key in dotfile and \
                    isinstance(dotfile[old_key], bool):
                # patch link_children: <bool>
                cur = dotfile[old_key]
                new = self.lnk_nolink
                if cur:
                    new = self.lnk_children
                del dotfile[old_key]
                dotfile[self.key_dotfile_link] = new
                self._dirty = True
                self._dirty_deprecated = True
                warn = 'deprecated \"link_children\" value'
                warn += ', updated to \"{}\"'.format(new)
                self._log.warn(warn)

    ########################################################
    # yaml utils
    ########################################################

    def _prepare_to_save(self, content):
        content = self._clear_none(content)

        # make sure we have the base entries
        if self.key_settings not in content:
            content[self.key_settings] = None
        if self.key_dotfiles not in content:
            content[self.key_dotfiles] = None
        if self.key_profiles not in content:
            content[self.key_profiles] = None
        return content

    def _load_yaml(self, path):
        """load a yaml file to a dict"""
        content = {}
        if self._debug:
            self._dbg('----------dump:{}----------'.format(path))
            cfg = '\n'
            with open(path, 'r', encoding='utf8') as file:
                for line in file:
                    cfg += line
            self._dbg(cfg.rstrip())
            self._dbg('----------end:{}----------'.format(path))
        try:
            content, fmt = self._yaml_load(path)
            self._config_format = fmt
        except Exception as exc:
            self._log.err(exc)
            err = 'config yaml error: {}'.format(path)
            raise YamlException(err) from exc
        if self._debug:
            self._dbg('format: {}'.format(self._config_format))
        return content

    def _validate(self, yamldict):
        """validate entries"""
        if not yamldict:
            return

        # check top entries
        for entry in self.top_entries:
            if entry not in yamldict:
                err = 'no {} entry found'.format(entry)
                self._log.err(err)
                raise YamlException('config format error: {}'.format(err))

        # check link_dotfile_default
        if self.key_settings not in yamldict:
            # no configs top entry
            return
        if not yamldict[self.key_settings]:
            # configs empty
            return

        # check settings values
        settings = yamldict[self.key_settings]
        if self.key_settings_link_dotfile_default not in settings:
            return
        val = settings[self.key_settings_link_dotfile_default]
        if val not in self.allowed_link_val:
            err = 'bad link value: {}'.format(val)
            self._log.err(err)
            self._log.err('allowed: {}'.format(self.allowed_link_val))
            raise YamlException('config content error: {}'.format(err))

    @classmethod
    def _yaml_load(cls, path):
        """load config file"""
        is_toml = path.lower().endswith(".toml")
        if is_toml:
            return cls.__toml_load(path), 'toml'
        return cls.__yaml_load(path), 'yaml'

    @classmethod
    def __yaml_load(cls, path):
        """load from yaml"""
        with open(path, 'r', encoding='utf8') as file:
            data = yaml()
            data.typ = 'rt'
            content = data.load(file)
        return content

    @classmethod
    def __toml_load(cls, path):
        """load from toml"""
        with open(path, 'r', encoding='utf8') as file:
            data = file.read()
        content = toml.loads(data)
        # handle inexistent dotfiles/profiles
        # since toml doesn't have a nul/nil/null/none
        if cls.key_dotfiles not in content:
            content[cls.key_dotfiles] = None
        if cls.key_profiles not in content:
            content[cls.key_profiles] = None
        return content

    @classmethod
    def _yaml_dump(cls, content, file, fmt='yaml'):
        """dump config file"""
        if fmt == 'toml':
            return cls.__toml_dump(content, file)
        if fmt == 'yaml':
            return cls.__yaml_dump(content, file)
        raise YamlException("unsupported format")

    @classmethod
    def __yaml_dump(cls, content, file):
        """dump to yaml"""
        data = yaml()
        data.default_flow_style = False
        data.indent = 2
        data.typ = 'rt'
        data.dump(content, file)

    @classmethod
    def __toml_dump(cls, content, file):
        """dump to toml"""
        toml.dump(content, file)

    ########################################################
    # templating
    ########################################################

    def _redefine_templater(self):
        """create templater based on current variables"""
        fufile = None
        fifile = None
        if Settings.key_func_file in self.settings:
            fufile = self.settings[Settings.key_func_file]
        if Settings.key_filter_file in self.settings:
            fifile = self.settings[Settings.key_filter_file]
        self._tmpl = Templategen(variables=self.variables,
                                 func_file=fufile,
                                 filter_file=fifile)

    def _template_item(self, item, exc_if_fail=True):
        """
        template an item using the templategen
        will raise an exception if template failed and exc_if_fail
        """
        if not Templategen.var_is_template(item):
            return item
        try:
            val = item
            while Templategen.var_is_template(val):
                val = self._tmpl.generate_string(val)
        except UndefinedException as exc:
            if exc_if_fail:
                raise exc
        return val

    def _template_list(self, entries):
        """template a list of entries"""
        new = []
        if not entries:
            return new
        for entry in entries:
            newe = self._template_item(entry)
            if self._debug and entry != newe:
                self._dbg('resolved: {} -> {}'.format(entry, newe))
            new.append(newe)
        return new

    def _template_dict(self, entries):
        """template a dictionary of entries"""
        new = {}
        if not entries:
            return new
        for k, val in entries.items():
            newv = self._template_item(val)
            if self._debug and val != newv:
                self._dbg('resolved: {} -> {}'.format(val, newv))
            new[k] = newv
        return new

    def _template_dotfiles_entries(self):
        """template dotfiles entries"""
        if self._debug:
            self._dbg('templating dotfiles entries')
        dotfiles = self.dotfiles.copy()

        # make sure no dotfiles path is None
        for dotfile in dotfiles.values():
            src = dotfile[self.key_dotfile_src]
            if src is None:
                dotfile[self.key_dotfile_src] = ''
            dst = dotfile[self.key_dotfile_dst]
            if dst is None:
                dotfile[self.key_dotfile_dst] = ''

        # resolve links before taking subset of
        # dotfiles to avoid issues in upper layer
        for dotfile in dotfiles.values():
            # link
            if self.key_dotfile_link in dotfile:
                # normalize the link value
                link = dotfile[self.key_dotfile_link]
                newlink = self._resolve_dotfile_link(link)
                dotfile[self.key_dotfile_link] = newlink

        #  only keep dotfiles related to the selected profile
        pdfs = []
        pro = self.profiles.get(self._profile, [])
        if pro:
            pdfs = list(pro.get(self.key_profile_dotfiles, []))

        # and any included profiles
        for addpro in self._inc_profiles:
            pro = self.profiles.get(addpro, [])
            if not pro:
                continue
            pdfsalt = pro.get(self.key_profile_dotfiles, [])
            pdfs.extend(pdfsalt)
            pdfs = uniq_list(pdfs)

        # if ALL is defined
        if self.key_all not in pdfs:
            # take a subset of the dotfiles
            newdotfiles = {}
            for k, val in dotfiles.items():
                if k in pdfs:
                    newdotfiles[k] = val
            dotfiles = newdotfiles

        for dotfile in dotfiles.values():
            # src
            src = dotfile[self.key_dotfile_src]
            newsrc = self.resolve_dotfile_src(src, templater=self._tmpl)
            dotfile[self.key_dotfile_src] = newsrc
            # dst
            dst = dotfile[self.key_dotfile_dst]
            newdst = self.resolve_dotfile_dst(dst, templater=self._tmpl)
            dotfile[self.key_dotfile_dst] = newdst

    def _rec_resolve_variables(self, variables):
        """recursive resolve variables"""
        var = self._enrich_vars(variables, self._profile)
        # use a separated templategen to handle variables
        # resolved outside the main config
        func_files = self.settings[Settings.key_func_file]
        filter_files = self.settings[Settings.key_filter_file]
        templ = Templategen(variables=var,
                            func_file=func_files,
                            filter_file=filter_files)
        for k in variables.keys():
            val = variables[k]
            while Templategen.var_is_template(val):
                val = templ.generate_string(val)
                variables[k] = val
                templ.update_variables(variables)
        if variables is self.variables:
            self._redefine_templater()

    def _get_profile_included_vars(self):
        """resolve profile included variables/dynvariables"""
        for _, val in self.profiles.items():
            if self.key_profile_include in val and \
                    val[self.key_profile_include]:
                new = []
                for entry in val[self.key_profile_include]:
                    new.append(self._tmpl.generate_string(entry))
                val[self.key_profile_include] = new

        # now get the included ones
        pro_var = self._get_profile_included_item(self.key_profile_variables)
        pro_dvar = self._get_profile_included_item(self.key_profile_dvariables)

        # the included profiles
        inc_profiles = []
        if self._profile and self._profile in self.profiles:
            pentry = self.profiles.get(self._profile)
            inc_profiles = pentry.get(self.key_profile_include, [])

        # exec incl dynvariables
        return inc_profiles, pro_var, pro_dvar

    ########################################################
    # helpers
    ########################################################

    def _clear_profile_vars(self, dic):
        """
        remove profile variables from dic if found inplace
        to avoid profile variables being overwriten
        """
        if not dic:
            return
        for k in self._profilevarskeys:
            dic.pop(k, None)

    def _parse_extended_import_path(self, path_entry):
        """Parse an import path in a tuple (path, fatal_not_found)."""
        if self._debug:
            self._dbg('parsing path entry {}'.format(path_entry))

        path, _, attribute = path_entry.rpartition(self.key_import_sep)
        fatal_not_found = attribute != self.key_import_ignore_key
        is_valid_attribute = attribute in ('', self.key_import_ignore_key)
        if not is_valid_attribute:
            # If attribute is not valid it can mean that:
            # - path_entry doesn't contain the separator, and attribute is set
            #   to the whole path by str.rpartition
            # - path_entry contains a separator, but it's in the file path, so
            #   attribute is set to whatever comes after the separator by
            #   str.rpartition
            # In both cases, path_entry is the path we're looking for.
            if self._debug:
                self._dbg('using attribute default values for path {}'
                          .format(path_entry))
            path = path_entry
            fatal_not_found = self.key_import_fatal_not_found
        elif self._debug:
            self._dbg('path entry {} has fatal_not_found flag set to {}'
                      .format(path_entry, fatal_not_found))
        return path, fatal_not_found

    def _handle_non_existing_path(self, path, fatal_not_found=True):
        """Raise an exception or log a warning to handle non-existing paths."""
        error = 'bad path {}'.format(path)
        if fatal_not_found:
            raise YamlException(error)
        self._log.warn(error)

    def _check_path_existence(self, path, fatal_not_found=True):
        """Check if a path exists, raising if necessary."""
        if os.path.exists(path):
            if self._debug:
                self._dbg('path {} exists'.format(path))
            return path

        self._handle_non_existing_path(path, fatal_not_found)
        # Explicit return for readability. Anything evaluating to false is ok.
        return None

    def _process_path(self, path_entry):
        """
        This method processed a path entry. Namely it:
        - Normalizes the path.
        - Expands globs.
        - Checks for path existence, taking in account fatal_not_found.
        This method always returns a list containing only absolute paths
        existing on the filesystem. If the input is not a glob, the list
        contains at most one element, otherwise it could hold more.
        """
        path, fatal_not_found = self._parse_extended_import_path(path_entry)
        path = self._norm_path(path)
        paths = self._glob_path(path) if self._is_glob(path) else [path]
        if not paths:
            if self._debug:
                self._dbg("glob path {} didn't expand".format(path))
            self._handle_non_existing_path(path, fatal_not_found)
            return []

        checked_paths = (self._check_path_existence(p, fatal_not_found)
                         for p in paths)
        return [p for p in checked_paths if p]

    def _resolve_paths(self, paths):
        """
        This function resolves a list of paths. This means normalizing,
        expanding globs and checking for existence, taking in account
        fatal_not_found flags.
        """
        processed_paths = (self._process_path(p) for p in paths)
        return list(chain.from_iterable(processed_paths))

    @classmethod
    def _merge_dict(cls, high, low, deep=False):
        """
        both dict must be the same form/type
        if deep is True, then merge recursively
        """
        if not high:
            high = {}
        if not low:
            low = {}
        if not high and not low:
            return {}

        if not deep:
            return {**low, **high}

        final = high.copy()
        for k, val in low.items():
            if isinstance(val, dict):
                # content is dict, recurse
                if k not in final:
                    final[k] = {}
                final[k] = cls._merge_dict(val, final[k], deep=True)
            elif isinstance(val, list):
                # content is list, merge
                if k not in final:
                    final[k] = []
                final[k] += val
            else:
                # don't know how to handle
                err = 'unable to merge'
                raise YamlException(err)
        return final

    @classmethod
    def _get_entry(cls, dic, key, mandatory=True):
        """return copy of entry from yaml dictionary"""
        if key not in dic:
            if mandatory:
                err = 'invalid config: no entry \"{}\" found'.format(key)
                raise YamlException(err)
            dic[key] = {}
            return deepcopy(dic[key])
        if mandatory and not dic[key]:
            # ensure is not none
            dic[key] = {}
        return deepcopy(dic[key])

    def _clear_none(self, dic):
        """recursively delete all none/empty values in a dictionary."""
        new = {}
        for k, val in dic.items():
            if k == self.key_dotfile_src:
                # allow empty dotfile src
                new[k] = val
                continue
            if k == self.key_dotfile_dst:
                # allow empty dotfile dst
                new[k] = val
                continue
            newv = val
            if isinstance(val, dict):
                # recursive travers dict
                newv = self._clear_none(val)
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

    @classmethod
    def _is_glob(cls, path):
        """Quick test if path is a glob."""
        return '*' in path or '?' in path

    def _glob_path(self, path):
        """Expand a glob."""
        if self._debug:
            self._dbg('expanding glob {}'.format(path))
        expanded_path = os.path.expanduser(path)
        return glob.glob(expanded_path, recursive=True)

    def _norm_path(self, path):
        """Resolve a path either absolute or relative to config path"""
        if not path:
            return path
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            dirn = os.path.dirname(self._path)
            ret = os.path.join(dirn, path)
            if self._debug:
                msg = 'normalizing relative to cfg: {} -> {}'
                self._dbg(msg.format(path, ret))
            path = ret
        ret = os.path.normpath(path)
        if self._debug and path != ret:
            self._dbg('normalizing: {} -> {}'.format(path, ret))
        return ret

    def _shell_exec_dvars(self, dic, keys=None):
        """shell execute dynvariables in-place"""
        if not keys:
            keys = dic.keys()
        for k in keys:
            val = dic[k]
            ret, out = shellrun(val, debug=self._debug)
            if not ret:
                err = 'var \"{}: {}\" failed: {}'.format(k, val, out)
                self._log.err(err)
                raise YamlException(err)
            if self._debug:
                self._dbg('{}: `{}` -> {}'.format(k, val, out))
            dic[k] = out

    @classmethod
    def _check_minversion(cls, minversion):
        if not minversion:
            return
        try:
            cur = ([int(x) for x in VERSION.split('.')])
            cfg = ([int(x) for x in minversion.split('.')])
        except Exception as exc:
            err = 'bad version: \"{}\" VS \"{}\"'.format(VERSION, minversion)
            raise YamlException(err) from exc
        if cur < cfg:
            err = 'current dotdrop version is too old for that config file.'
            err += ' Please update.'
            raise YamlException(err)

    def _debug_entries(self):
        """debug print all interesting entries"""
        if not self._debug:
            return
        self._dbg('Current entries')
        self._debug_dict('entry settings', self.settings)
        self._debug_dict('entry dotfiles', self.dotfiles)
        self._debug_dict('entry profiles', self.profiles)
        self._debug_dict('entry actions', self.actions)
        self._debug_dict('entry trans_r', self.trans_r)
        self._debug_dict('entry trans_w', self.trans_w)
        self._debug_dict('entry variables', self.variables)

    def _debug_dict(self, title, elems):
        """pretty print dict"""
        if not self._debug:
            return
        self._dbg('{}:'.format(title))
        if not elems:
            return
        for k, val in elems.items():
            if isinstance(val, dict):
                self._dbg('  - \"{}\"'.format(k))
                for subkey, sub in val.items():
                    self._dbg('    * {}: \"{}\"'.format(subkey, sub))
            else:
                self._dbg('  - \"{}\": {}'.format(k, val))

    def _dbg(self, content):
        directory = os.path.basename(os.path.dirname(self._path))
        pre = os.path.join(directory, os.path.basename(self._path))
        self._log.dbg('[{}] {}'.format(pre, content))

    def _save_uservariables(self, uvars):
        """save uservariables to file"""
        parent = os.path.dirname(self._path)
        # find a unique path
        path = None
        cnt = 0
        while True:
            if cnt == 0:
                name = self.save_uservariables_name.format('')
            else:
                name = self.save_uservariables_name.format('-{}'.format(cnt))
            cnt += 1

            path = os.path.join(parent, name)
            if not os.path.exists(path):
                break

        # save the config
        content = {'variables': uvars}
        try:
            if self._debug:
                self._dbg('saving uservariables values to {}'.format(path))
            with open(path, 'w', encoding='utf8') as file:
                self._yaml_dump(content, file, fmt=self._config_format)
        except Exception as exc:
            # self._log.err(exc)
            err = 'error saving uservariables to {}'.format(path)
            self._log.err(err)
            raise YamlException(err) from exc
        self._log.log('uservariables values saved to {}'.format(path))
