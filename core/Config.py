#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of EasyExp
#
# Copyright (C) 2015 Florian Perdreau, Radboud University Nijmegen
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

"""
ExpFrame is a Python framework designed for making programing of behavioral experiments easier and more automatic.
"""

__author__ = "Florian Perdreau"
__copyright__ = "Copyright 2015, Florian Perdreau"
__license__ = "GPL"
__version__ = "0.9.5"
__maintainer__ = "Florian Perdreau"
__email__ = "f.perdreau@donders.ru.nl"
__status__ = "Production"

# IMPORTS
# =======
# Import useful libraries
from os import mkdir
from os.path import isdir, isfile

# Data I/O
import json

# Dialog UI
from .gui.dialog import DialogGUI


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

    def __init__(self, rootfolder='/', expname=''):
        """
        Constructor of Config Class
        :param rootfolder: path to root folder
        :type rootfolder: str
        :param expname: experiment's name
        :type expname: str
        """
        self.expname = expname
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
                    print('[{}] Creating Folder "{}"'.format(__name__, folder))
                except Exception as e:
                    print('[{}] Could not create folder "{}"'.format(__name__, folder))
                    raise e
        return True

    def loadSetting(self):
        """
        load settings from config file
        :return:
        """
        self.settingsFile.load()
        self.settings = self.settingsFile.data

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
        self.settingsFile.display()
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
                print('[{}] Could not open "{}"'.format(__name__, self.pathtofile))
                raise e
        else:
            print("[{}] The settings file '{}' cannot be found!".format(__name__, self.pathtofile))
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
                print('[{}] Could not write into "{}"'.format(__name__, self.pathtofile))

    def display(self):
        """
        Get experiment's settings
        """
        expinfo = DialogGUI(self.data)
        self.data = {}
        for key, value in expinfo.out.iteritems():
            setattr(self, key, expinfo.out[key])
            self.data[key] = expinfo.out[key]
