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
import json
import time
from os import mkdir, remove
from os.path import isdir, isfile, join

# GUI
from gui.gui_wrapper import GuiWrapper

# Logger
import logging
logger = logging.getLogger("EasyExp")


class User(object):
    """
    User class
    This class handles participant's information and related methods to read or update information from/into the info
    file found in the user's data folder
    - Initials
    - Fullname
    - Age
    - Handedness
    - Dominant Eye (for eye tracking purpose)
    - Date/time
    - Datafile information
    - file I/O methods (load, save)
    """

    def __init__(self, data_folder, expname, session=1, demo=False, practice=False):
        """
        Constructor of User class
        :param data_folder: path to data folder
        :type data_folder: str
        :param expname: experiment name (format: name_version. E.g.: 'my_experiment_v1-0-0')
        :type expname: str
        :param session: session number
        :type session: int
        :param demo: does the experiment run in demo mode
        :type demo: bool
        :param practice: practice mode (create a special design file labeled "practice")
        :type practice: bool
        """
        self.practice = practice
        self.expname = expname
        self.demo = demo
        self.session = session
        self.__logger = logger

        # Subject information
        # ===================
        self.age = 0
        self.hand = 'r'
        self.eye = 'r'
        self.dEye = 0.061
        self.exist = 0
        self.date = time.strftime("%d-%m-%y")
        self.name = 'demo'
        self.gender = 'm'

        self.starttime = time.time()

        # Subject folders
        # ===============
        self.datafolder = data_folder
        self.base_file_name = None  # Base file name ("expname_session_(practice)")
        self.subfolder = None  # Subject folder
        self.infofile = None  # subject information file
        self.designfile = None  # subject design file
        self.datafilename = None  # subject data filename
        self.logfilename = None  # Log file
        self.defaultfieldsname = None  # default fields name
        self.dftName = None  # subject default file name

    def __str__(self):
        """
        Print method: shows user's information
        :return: string
        """
        return "\n--- Subject information ---\n" \
               "\tName: {0}\n" \
               "\tAge: {1}\n" \
               "\tHandedness: {2}\n" \
               "\tEye: {3}\n" \
               "\tFiles:\n" \
               "\t\tInformation file: {4}\n" \
               "\t\tdata file: {5}\n" \
               "\t\tDesign file: {6}\n".format(self.name, self.age, self.hand, self.eye, self.infofile,
                                               self.datafilename, self.designfile)

    def setup(self, cli):
        """
        Get user's information
        """
        # Get name if not demo mode. Otherwise, use default name
        if self.demo is False:
            self.name = self.get_user_name(cli)

        # Set folders and files
        self.subfolder = join(self.datafolder, self.name)
        self.infofile = join(self.subfolder, "{}_info.txt".format(self.name))
        self.dftName = join(self.subfolder, '{}_{}_{}'.format(self.name, self.expname, self.session))
        self.base_file_name = '{}_{}'.format(self.expname, self.session)

        # Append "practice" to practice data files
        if self.practice:
            self.dftName = "{}_practice".format(self.dftName)
            self.base_file_name = "{}_practice".format(self.base_file_name)

        self.designfile = "{}_design.txt".format(self.dftName)
        self.datafilename = '{}_data.txt'.format(self.dftName)
        self.logfilename = '{}_log.log'.format(self.dftName)

        # Delete previous data and design files if running in demo mode
        if self.demo:
            self.__clean_files()

        # Make new user
        self.make(cli)

    def __clean_files(self):
        """
        Delete previous data and design files
        :return:
        """
        for file_to_delete in [self.designfile, self.datafilename]:
            if isfile(file_to_delete):
                try:
                    remove(file_to_delete)
                except IOError as e:
                    self.__logger.warning('Could not delete previous data and design files: {}'.format(e))

    def __check_user(self):
        """
        Check if user exists
        :return: int: (0) if user does not already exist,(1) if user's folder exists, (2) if user's folder and info file exist.
        """
        if isdir(self.subfolder):
            self.exist = 1
            # Does this folder include an info file?
            if isfile(self.infofile):
                self.exist = 2
        else:
            self.exist = 0
        return self.exist

    def make(self, cli):
        """
        Create user: If either the info file is missing or the subject's folder does not exist yet
        """
        # Check if user already exists
        self.__check_user()
        if self.exist != 2:
            if self.exist == 0:
                # We create the folder
                mkdir(self.subfolder)
                self.exist = 1
            self.getinfo(cli)
        # Else, we simply load and read the info file and display its content.
        else:
            logger.info("[{}] User '{}' already exists.".format(__name__, self.name))
            logger.info("[{}] Loading information".format(__name__))
            self.loadinfo()
        logger.info(self)

    def get_user_name(self, cli):
        """
        Show Tkinter dialog to get subject's initials
        :rtype : str User's initials
        """
        fields = {'initials': self.name}
        if cli:
            info = GuiWrapper.factory(cli, 'simple', fields, title="Participant Initials", mandatory=True)
        else:
            info = GuiWrapper.factory(cli, 'simple', fields, title="Participant Initials")

        return info.out['initials'].upper()

    def getinfo(self, cli):
        """
        Show Tkinter dialog to get subject's information
        :rtype : object: instance of User
        """
        fields = {'date': self.date, 'name': self.name, 'age': self.age, 'hand': self.hand, 'eye': self.eye,
                  'dEye': self.dEye, 'gender': self.gender}

        if not cli:
            info = GuiWrapper.factory(cli, 'simple', fields, title="Participant info")
        else:
            info = GuiWrapper.factory(cli, 'simple', fields, title="Participant info", mandatory=True)

        datatowrite = {}
        for key, value in info.out.iteritems():
            setattr(self, key, value)
            datatowrite[key] = value

        # We write subject's info in a file
        with open(self.infofile, 'w', 0) as fid:
            json.dump(datatowrite, fid, indent=4)

    def loadinfo(self):
        """
        Loading user information from user's info file
        :rtype : object: instance of User
        """
        json_info = open(self.infofile, 'r')
        subinfo = json.load(json_info)
        for key, value in subinfo.iteritems():
            setattr(self, key, subinfo[key])
        json_info.close()
