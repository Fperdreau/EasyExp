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
EasyExp is a Python framework designed to ease the implementation of behavioral experiments.
"""

__author__ = "Florian Perdreau"
__copyright__ = "Copyright 2016, Florian Perdreau"
__license__ = "GPL"
__version__ = "0.9.0"
__maintainer__ = "Florian Perdreau"
__email__ = "f.perdreau@donders.ru.nl"
__status__ = "Development"

# IMPORTS
# =======
# Core
from .Config import Config
from .User import User
from .Design import Design
from .Trial import Trial
from .Screen import Screen

# Import useful libraries
import time
import sys
from os import listdir
from os.path import isdir, join

# Dialog UI
from .gui.dialog import DialogGUI

# Logger
from .system.customlogger import CustomLogger


class Core(object):
    """
    Class ExpCore
    - handle User, Config, Trial instances

    Usage:
    >>> from core.Core import Core
    >>> root_folder = 'path/to/application_root_folder/'
    >>># Create new experiment
    >>>Exp = Core()
    >>>
    >>># Initialize experiment
    >>>Exp.init(root_folder, custom=True)

    >>># Open main window and run the experiment
    >>>Exp.run()
    """
    appname = "ExpFrame"
    version = __version__
    logger = None

    def __init__(self):
        """
        ExpCore constructor
        :return:
        """

        self.config = None
        self.user = None
        self.trial = None
        self.screen = None
        self.window = None
        self.design = None

        self.folders = {'rootFolder': None, 'data': None, 'expFolder': None}
        self.files = {}
        self.experimentsFolder = None
        self.status = True

        self.timer = None
        self.startTime = None
        self.stopTime = None

        self.expname = None

    def get_logger(self):
        """
        Logger factory
        Returns
        -------
        rtype: CustomLogger
        """
        if not Core.logger:
            Core.logger = CustomLogger(__name__, file_name=self.experimentsFolder, level='warning')
        return Core.logger

    def getexp(self, folder):
        """
        Provide the user with a dialog UI to choose the experiment to run
        :return:
        """
        # Folders to exclude
        dirs_list = {f for f in listdir(folder) if isdir(join(folder, f))}
        selectexp = DialogGUI({'expname': dirs_list}, 'Select Experiment')
        return selectexp.out['expname']

    def init(self, rootfolder, custom=False):
        """
        Initialize dependencies
        :param string rootfolder: full path to root folder
        :type rootfolder: str
        :param custom: import custom design from custom_design.py
        :type custom: bool
        """
        print("\n##############################\n")
        print("# Welcome to {} (version {})\n".format(self.appname, __version__))
        print("# {}\n".format(__copyright__))
        print("# Date: {}".format(time.strftime("%d-%m-%y %H:%M:%S")))
        print("\n##############################\n")

        self.experimentsFolder = "{}/experiments/".format(rootfolder)
        self.expname = self.getexp(self.experimentsFolder)

        # Get and set configuration
        config = Config(rootfolder=rootfolder, expname=self.expname)
        config.setup()
        self.config = config.settings
        self.folders = config.folders
        self.files = config.files

        # Create user
        self.user = User(datafolder=self.folders['data'], expname=self.expname, session=self.config['session'],
                         demo=self.config['demo'], practice=self.config['practice'])
        self.user.setup()
        self.files['design'] = self.user.designfile

        # Make factorial design
        self.design = Design(expname=self.expname, conditionfile=self.files['conditions'],
                             userfile=self.files['design'], demo=self.config['demo'], practice=self.config['practice'],
                             max_trials=self.config['max_trials'], custom=custom, folder=self.folders['expFolder'])
        self.design.make()

        # Screen
        self.screen = Screen(display_type=self.config['display_type'], resolution=self.config['resolution'],
                             size=self.config['size'], distance=self.config['distance'],
                             fullscreen=self.config['fullscreen'], bgcolor=self.config['bgcolor'],
                             expfolder=self.folders['expFolder'])

    def run(self):
        """
        Run and time experiment
        """

        print("\n--- Start Experiment: '{}' ---\n\n".format(self.expname))

        # Import experiment class from experiment's folder (e.g.: experiments/experiment_name/runtrial.py)
        sys.path.append(self.folders['expFolder'])
        try:
            from runtrial import RunTrial
        except ImportError as e:
            print('[{}] Could not import RunTrial')
            raise e

        # Start timer
        self.timer = time.time()
        self.startTime = self.timer

        # Open window
        self.screen.open()

        # Instantiate Trial and experiment
        self.trial = Trial(design=self.design, settings=self.config, userfile=self.user.datafilename,
                           paramsfile=self.files['parameters'], pause_interval=int(self.config['pauseInt']))
        runtrial = RunTrial(trial=self.trial, screen=self.screen, user=self.user)

        # Run experiment
        try:
            if self.screen.display_type == 'qt':
                self.screen.ptw.setExperiment(runtrial)
                # Enter main loop (the underscore prevents using the keyword)
                sys.exit(self.screen.QTapp.exec_())
            elif self.screen.display_type == 'psychopy':
                runtrial.run()
        except (Exception, TypeError) as e:
            print('[{}] An unexpected error has occurred')
            raise e

        # Stop experiment
        self.stop()

    def stop(self):
        """
        Stop experiment
        """
        if self.screen.display_type == 'psychopy':
            self.screen.close()
        self.stopTime = time.time()

        duration = round((self.stopTime - self.startTime) / 60)
        print("\n--- End of Experiment '{}' ---"
              "\nTotal duration: {} minutes"
              "\n---\n".format(self.expname, duration))