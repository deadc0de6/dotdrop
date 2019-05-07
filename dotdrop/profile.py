#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# flake8: noqa

# from operator import attrgetter
#
# import yaml
#
# from .dotfile import Dotfile
#
#
# class Profile:
#     """Represent a profile."""
#
#     @staticmethod
#     def parse_imported_dotfiles(imported_dotfiles):
#         dotfiles_names = []
#
#         for file_name in imported_dotfiles:
#             with open(file_name, 'r') as dotfiles_file:
#                 dotfiles_yaml = yaml.safe_load(dotfiles_file)
#
#             try:
#                 dotfile_names.extend(dotfiles_yaml['dotfiles'])
#             except KeyError:
#                 raise KeyError('{} dotfile file is missing "dotfiles" key'
#                                .format(file_name))
#
#         return dotfile_names
#
#     @classmethod
#     def parse(cls, cfg, yaml_dict):
#         if isinstance(yaml_dict, str):
#             yaml_file_name = yaml_dict
#             with open(yaml_file_name, 'r') as yaml_file:
#                 yaml_dict = yaml.safe_load(yaml_file)
#
#         try:
#             name = next(yaml_dict.keys())
#         except StopIteration:
#             raise ValueError('Empty profile')
#
#         profile = yaml_dict[name]
#
#         try:
#             dotfiles = profile['dotfiles']
#         except KeyError:
#             raise KeyError('Profile {} has no dotfile'.format(name))
#
#         try:
#             variables = profile['variables']
#         except KeyError:
#             pass
#
#         try:
#             dynvariables = profile['dynvariables']
#         except KeyError:
#             pass
#
#         try:
#             dotfiles_from_file = profile['imported_dotfiles']
#             imported_dotfiles = cls.parse_imported_dotfiles(
#             dotfiles_from_file)
#         except KeyError:
#             pass
#
#         return cls(cfg, name, dotfiles=dotfiles, included_profiles=(),
#                    variables=variables, dynvariables=dynvariables,
#                    imported_dotfiles=imported_dotfiles)
#
#     def __init__(self, cfg, name, dotfiles=None, included_profiles=None,
#                  variables=None, dynvariables=None, imported_dotfiles=None):
#         self.cfg = cfg
#         self.name = name
#         self.dotfiles = dotfiles or []
#         self.dynvariables = dynvariables or {}
#         self.imported_dotfiles = imported_dotfiles or []
#         self.included_profiles = included_profiles or []
#         self.variables = variables or {}
#
#         self.own_dotfiles = dotfiles.copy()
#
#     @property
#     def external_dotfiles(self):
#         return list(set(self.dotfiles) - set(self.own_dotfiles))
#
#     def add_dotfiles(self, dotfiles, own=False):
#         try:
#             iter(dotfiles)
#             add = list.extend
#         except TypeError:
#             add = list.append
#         #
#         #
#         # add(self.dotfiles, )
#         #
#         #
#         assert isinstance(dotfile, Dotfile)
#         self.dotfiles.append(dotfile)
#         if own:
#             self.own_dotfiles.append(dotfile)
#
#     def serialize(self):
#         dic = {
#             'dotfiles': map(attrgetter('key'), self.own_dotfiles),
#         }
#         if self.included_profiles:
#             dic['include'] = map(attrgetter('name'), self.included_profiles)
#         if self.variables:
#             dic['variables'] = self.variables
#         if self.dynvariables:
#             dic['dynvariables'] = self.dynvariables
#         if self.imported_dotfiles:
#             dic['import'] = self.imported_dotfiles
#
#         return {
#             self.name: dict
#         }
