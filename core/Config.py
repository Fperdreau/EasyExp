#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of EasyExp
#
# Copyright (C) 2016 Florian Perdreau, Radboud University Nijmegen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

# IMPORTS
# =======
# Import useful libraries
from os import mkdir
from os.path import isdir, isfile

# EasyExp

# Data I/O
import json

# Dialog UI
from core.gui.gui_wrapper import GuiWrapper
import logging


class Config(object):
    """
    This class handles methods to read, parse and update experiment's settings and configuration files.
    It creates folders needed by the framework (data folder, analyses folder and user folder) if they do not exist yet.
    Experiment setup
    - Creation of useful folders (data,analyses,user)
    - Get environmental settings
    - Get experiment's settings

    :required: settings.json
    """

    def __init__(self, rootfolder='/', expname='', cli=False):
        """
        Constructor of Config Class
        :param rootfolder: path to root folder
        :type rootfolder: str
        :param expname: experiment's name
        :type expname: str
        """
        self.expname = expname
        self.__cli = cli
        self.__logger = logging.getLogger('EasyExp')

        self.folders = {
            'rootFolder': rootfolder,
            'experimentFolder': "{}/experiments".format(rootfolder),
            'expFolder': "{}/experiments/{}".format(rootfolder, expname)
        }

        self.files = {
            'settings': "{}/settings.json".format(self.folders['expFolder']),
            'conditions': "{}/conditions.json".format(self.folders['expFolder']),
            'parameters': '{}/parameters.json'.format(self.folders['expFolder'])
        }

        self.settingsFile = ConfigFiles(self.files['settings'])
        self.settings = {}

        # Create necessary folders
        self.createfolders()

    def setup(self):
        """
        This function loads settings from the experiment's 'settings.json' file, renders a GUI form to invite the user
        modifying the settings and update the settings file accordingly.
        """
        self.loadSetting()  # Load existing settings
        self.getexpsetting()  # Display settings and allow user to modify them
        if len(self.settings) > 0:
            self.saveSettings()  # Save settings
        self.dispatch()

    def createfolders(self):
        """
        Creates necessary folders and get list of useful folders (data, functions, config)
        :rtype : bool
        """
        self.folders['data'] = "%s/data" % self.folders['rootFolder']
        self.folders['libs'] = "%s/libs" % self.folders['rootFolder']
        self.folders['analyses'] = "%s/analyses" % self.folders['rootFolder']

        for key, folder in self.folders.iteritems():
            if isdir(folder) == 0:
                try:
                    mkdir(folder)
                    self.__logger.info('[{}] Creating Folder "{}"'.format(__name__, folder))
                except Exception as e:
                    self.__logger.critical('[{}] Could not create folder "{}"'.format(__name__, folder))
                    raise e
        return True

    def loadSetting(self):
        """
        load settings from config file
        :return:
        """
        self.settingsFile.load()

    def dispatch(self):
        for section, setting in self.settingsFile.data.iteritems():
            self.settings[section] = Section(setting)

    def saveSettings(self):
        """
        Save settings
        :return:
        """
        self.settingsFile.save()

    def getexpsetting(self):
        """
        Get experiment's settings
        """
        self.settingsFile.display(cli=self.__cli)
        self.settings = self.settingsFile.data


class Section(dict):

    def __init__(self, data):
        super(Section, self).__init__()
        self._data = data

    def __getitem__(self, item):
        if item in self._data and 'value' in self._data[item]:
            return self._data[item]['value']
        else:
            raise KeyError('Setting {} does not exist'.format(item))


class ConfigFiles(object):
    """
    ConfigFiles class
    Handles configuration files and their corresponding methods: load, save and display
    """

    def __init__(self, pathtofile):
        """
        ConfigFiles constructor
        :param string pathtofile: full path to config file
        :return: void
        """
        self.pathtofile = pathtofile
        self.data = {}

    def load(self):
        """
        load settings from config file
        :return:
        """
        if isfile(self.pathtofile):
            try:
                json_info = open(self.pathtofile, 'r')
                self.data = json.load(json_info)
                json_info.close()
            except IOError as e:
                msg = IOError('[{}] Could not open "{}": {}'.format(__name__, self.pathtofile, e))
                logging.getLogger('EasyExp').critical(msg)
                raise msg
        else:
            msg = IOError("[{}] The settings file '{}' cannot be found!".format(__name__, self.pathtofile))
            logging.getLogger('EasyExp').critical(msg)
            raise msg
        return self.data

    def save(self):
        """
        Save settings
        :return:
        """
        if isfile(self.pathtofile):
            try:
                with open(self.pathtofile, 'w', 0) as fid:
                    json.dump(self.data, fid, indent=4)
            except IOError as e:
                msg = IOError('[{}] Could not write into "{}": {}'.format(__name__, self.pathtofile, e))
                logging.getLogger('EasyExp').critical(msg)
                raise msg

    def display(self, cli=False):
        """
        Get experiment's settings
        """
        if cli:
            expinfo = GuiWrapper.factory(cli, 'nested', self.data, title="Experiment setup", mandatory=False)
        else:
            expinfo = GuiWrapper.factory(cli, 'nested', self.data, title="Experiment setup")

        self.data = expinfo.out
