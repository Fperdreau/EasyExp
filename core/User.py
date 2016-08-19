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
import time
from os import mkdir
from os.path import isdir, isfile

# Data I/O
import json

# Dialog UI
from .gui.dialog import DialogGUI

# Logger
from .system.customlogger import CustomLogger


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

    def __init__(self, datafolder='', expname='', session=1, demo=False, practice=False):
        """
        Constructor of User class
        :param datafolder: path to data folder
        :param expname: experiment name
        :param session: session number
        :param demo: does the experiment run in demo mode
        :param practice: practice mode (create a special design file labeled "practice")
        """
        self.practice = practice
        self.expname = expname
        self.demo = demo
        self.session = session

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
        self.datafolder = datafolder
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

    def setup(self):
        """
        Get user's information
        """
        # Get name if not demo mode. Otherwise, use default name
        if self.demo is False:
            self.name = self.get_user_name()

        # Set folders and files
        self.subfolder = "%s/%s" % (self.datafolder, self.name)
        self.infofile = "%s/%s_info.txt" % (self.subfolder, self.name)
        if not self.practice:
            self.dftName = '{}/{}_{}_{}'.format(self.subfolder, self.name, self.expname, self.session)
            self.base_file_name = '{}_{}'.format(self.expname, self.session)
        else:
            self.dftName = '{}/{}_{}_{}_practice'.format(self.subfolder, self.name, self.expname, self.session)
            self.base_file_name = '{}_{}_practice'.format(self.expname, self.session)

        self.designfile = "{}_design.txt".format(self.dftName)
        self.datafilename = '{}_data.txt'.format(self.dftName)
        self.logfilename = '{}_log.txt'.format(self.dftName)

        self.make()

    def checkuser(self):
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

    def make(self):
        """
        Create user: If either the info file is missing or the subject's folder does not exist yet
        """
        # Check if user already exists
        self.checkuser()
        if self.exist != 2:
            if self.exist == 0:
                # We create the folder
                mkdir(self.subfolder)
                self.exist = 1
            self.getinfo()
        # Else, we simply load and read the info file and display its content.
        else:
            print("[{}] User '{}' already exists.".format(__name__, self.name))
            print("[{}] Loading information".format(__name__))
            self.loadinfo()
        print(self)

    def get_user_name(self):
        """
        Show Tkinter dialog to get subject's initials
        :rtype : str User's initials
        """
        fields = {'initials': self.name}
        info = DialogGUI(fields)
        return info.out['initials']

    def getinfo(self):
        """
        Show Tkinter dialog to get subject's information
        :rtype : object: instance of User
        """
        fields = {'date': self.date, 'name': self.name, 'age': self.age, 'hand': self.hand, 'eye': self.eye,
                  'dEye': self.dEye, 'gender': self.gender}
        info = DialogGUI(fields)

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
