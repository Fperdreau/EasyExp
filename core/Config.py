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
from os.path import isdir, isfile, join

# EasyExp

# Data I/O
import json

# Dialog UI
from gui.gui_wrapper import GuiWrapper
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

    # Default settings
    __defaults = {
            "setup": {
                "custom": {
                    "type": "checkbox",
                    "options": [
                        True,
                        False
                    ],
                    "value": False,
                    "label": "Custom design"
                },
                "pauseInt": {
                    "type": "text",
                    "value": 30,
                    "label": "Break interval"
                },
                "pauseDur": {
                    "type": "text",
                    "value": 0,
                    "label": "Break duration"
                },
                "pauseMode": {
                    "type": "select",
                    "value": "time",
                    "label": "Break mode",
                    "options": [
                        "time",
                        "count"
                    ]
                },
                "movie": {
                    "type": "checkbox",
                    "options": [
                        True,
                        False
                    ],
                    "value": False,
                    "label": "Movie"
                },
                "practice": {
                    "type": "checkbox",
                    "options": [
                        True,
                        False
                    ],
                    "value": False,
                    "label": "Practice"
                },
                "max_trials": {
                    "type": "text",
                    "value": 30,
                    "label": "# practice trials"
                },
                "session": {
                    "type": "text",
                    "value": 1,
                    "label": "Session ID"
                },
                "demo": {
                    "type": "checkbox",
                    "options": [
                        True,
                        False
                    ],
                    "value": True,
                    "label": "Demo"
                }
            },
            "display": {
                "distance": {
                    "type": "text",
                    "value": 1470.0,
                    "label": "Distance"
                },
                "fullscreen": {
                    "type": "checkbox",
                    "options": [
                        True,
                        False
                    ],
                    "value": False,
                    "label": "Full screen"
                },
                "bgcolor": {
                    "type": "text",
                    "value": [
                        -1.0,
                        -1.0,
                        -1.0
                    ],
                    "label": "Background color"
                },
                "display_type": {
                    "type": "select",
                    "options": [
                        "psychopy",
                        "qt",
                        "pygame"
                    ],
                    "value": "psychopy",
                    "label": "Display type"
                },
                "freq": {
                    "type": "text",
                    "value": 60,
                    "label": "frequency"
                },
                "resolution": {
                    "type": "text",
                    "value": [
                        1920.0,
                        1080.0
                    ],
                    "label": "Resolution"
                },
                "size": {
                    "type": "text",
                    "value": [
                        1206.0,
                        679.0
                    ],
                    "label": "Screen size"
                }
            }
        }

    def __init__(self, rootfolder, expname, cli=False):
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
            'experimentFolder': join(rootfolder, 'experiments'),
            'expFolder': join(rootfolder, 'experiments', expname)
        }

        self.files = {
            'settings': join(self.folders['expFolder'], 'settings.json'),
            'conditions': join(self.folders['expFolder'], 'conditions.json'),
            'parameters': join(self.folders['expFolder'], 'parameters.json')
        }

        self.settingsFile = ConfigFiles(self.files['settings'])
        self.settings = {}

        # Create necessary folders
        self.__create_folders()

    def setup(self):
        """
        This function loads settings from the experiment's 'settings.json' file, renders a GUI form to invite the user
        modifying the settings and update the settings file accordingly.
        """
        self.__load_setting()  # Load existing settings
        self.__get_setting()  # Display settings and allow user to modify them
        if len(self.settings) > 0:
            self.save_settings()  # Save settings
        self.__dispatch()

    @staticmethod
    def __merge(source, destination):
        """
        Update and override key/value pair of source dictionary with key/value pairs of destination dictionary
        :param source: referent dictionary
        :type source: dict
        :param destination: dictionary to update
        :type destination: dict
        :return:
        """
        for key, value in source.iteritems():
            if key not in destination:
                destination.update({key: value})
        return destination

    @staticmethod
    def __match(reference, to_update):
        """
        Match key/value pair of 1st dictionary with key/value pairs of 2nd dictionary. Key/value pairs of first
        dictionary not present in second dictionary will be deleted.
        :param reference: referent dictionary
        :type reference: dict
        :param to_update: dictionary to update
        :type to_update: dict
        :return:
        """
        for key, value in to_update.iteritems():
            if key not in reference:
                del to_update[key]
        return to_update

    def __create_folders(self):
        """
        Creates necessary folders and get list of useful folders (data, functions, config)
        :rtype : bool
        """
        self.folders['data'] = join(self.folders['rootFolder'], 'data')
        self.folders['libs'] = join(self.folders['rootFolder'], 'libs')
        self.folders['analyses'] = join(self.folders['rootFolder'], 'analyses')

        for key, folder in self.folders.iteritems():
            if isdir(folder) == 0:
                try:
                    mkdir(folder)
                    self.__logger.info('[{}] Creating Folder "{}"'.format(__name__, folder))
                except Exception as e:
                    self.__logger.critical('[{}] Could not create folder "{}"'.format(__name__, folder))
                    raise e
        return True

    def __load_setting(self):
        """
        load settings from config file
        :return:
        """
        self.settingsFile.load()
        self.settingsFile.data = self.__merge(self.__defaults, self.settingsFile.data)

    def __dispatch(self):
        """
        Dispatch settings
        :return:
        """
        self.settings = dict()
        for section, items in self.settingsFile.data.iteritems():
            if section not in self.settings:
                self.settings[section] = dict()

            for item, info in items.iteritems():
                if item not in self.settings[section]:
                    self.settings[section].update({item: info['value']})

    def save_settings(self):
        """
        Save settings
        :return:
        """
        self.settingsFile.save()

    def __get_setting(self):
        """
        Get experiment's settings
        """
        self.settingsFile.display(cli=self.__cli)
        self.settings = self.settingsFile.data


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
        self.__data = dict()

    def load(self):
        """
        load settings from config file
        :return:
        """
        if isfile(self.pathtofile):
            try:
                json_info = open(self.pathtofile, 'r')
                self.__data = json.load(json_info)
                json_info.close()
            except IOError as e:
                msg = IOError('[{}] Could not open "{}": {}'.format(__name__, self.pathtofile, e))
                logging.getLogger('EasyExp').critical(msg)
                raise msg
        else:
            msg = IOError("[{}] The settings file '{}' cannot be found!".format(__name__, self.pathtofile))
            logging.getLogger('EasyExp').critical(msg)
            raise msg
        return self.__data

    def save(self):
        """
        Save settings
        :return:
        """
        if isfile(self.pathtofile):
            try:
                with open(self.pathtofile, 'w', 0) as fid:
                    json.dump(self.__data, fid, indent=4)
            except IOError as e:
                msg = IOError('[{}] Could not write into "{}": {}'.format(__name__, self.pathtofile, e))
                logging.getLogger('EasyExp').critical(msg)
                raise msg

    def display(self, cli=False):
        """
        Get experiment's settings
        :param cli: use CLI or dialog window
        :type cli: bool
        """
        if cli is True:
            info = GuiWrapper.factory(cli, 'nested', self.data, title="Experiment setup", mandatory=False)
        else:
            info = GuiWrapper.factory(cli, 'nested', self.data, title="Experiment setup")
        self.__data = info.out

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = value
