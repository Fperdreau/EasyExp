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


"""
EasyExp is a Python framework designed to ease the implementation of behavioral experiments.
"""

# IMPORTS
# =======
# Version
import core.version as v

# Core
from .Config import Config
from .User import User
from .Design import Design
from .Trial import Trial
from .Screen import Screen

# Import useful libraries
import time
import sys
from os import listdir, mkdir
from os.path import isdir, join

# Dialog UI
from core.gui.gui_wrapper import GuiWrapper

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
    appname = "EasyExp"
    version = v.__version__
    __logger = None

    def __init__(self):
        """
        ExpCore constructor
        :return:
        """

        self.config = None
        self.user = None
        self.trial = None
        self.screen = None
        self.design = None

        self.__cli = False

        self.folders = {'rootFolder': None, 'data': None, 'expFolder': None}
        self.files = dict()
        self.experimentsFolder = None
        self.status = True
        self.settings = None

        self.startTime = None
        self.stopTime = None

        self.expname = None

    def getexp(self, folder):
        """
        Provide the user with a dialog UI to choose the experiment to run
        :return:
        """
        # Folders to exclude
        dirs_list = [f for f in listdir(folder) if isdir(join(folder, f))]
        data = {'Experiment selection': {
            'expname': {
                'value': dirs_list[0],
                'options': dirs_list,
                'type': 'select',
                'label': 'Select an experiment'
            }
        }}

        if self.cli:
            selectexp = GuiWrapper.factory(self.cli, 'nested', data, title='Select Experiment', mandatory=True)
        else:
            selectexp = GuiWrapper.factory(self.cli, 'nested', data, title='Select Experiment')
        return selectexp.out['Experiment selection']['expname']['value']

    @staticmethod
    def get_logger(rootfolder, expname):
        """
        Get application logger
        :param rootfolder:
        :param expname:
        :return:
        """
        if Core.__logger is None:
            # Set application's logger
            log_file = '{}/logs/{}_{}.log'.format(rootfolder, expname, time.strftime("%d%m%y_%H%M%S"))
            Core.__logger = CustomLogger(Core.appname, file_name=log_file, level='debug')
        return Core.__logger

    def init(self, rootfolder, custom=False, cli=False):
        """
        Initialize dependencies
        :param string rootfolder: full path to root folder
        :type rootfolder: str
        :param custom: import custom design from custom_design.py
        :type custom: bool
        :param cli: Run in command line (True)
        :type cli: bool
        """
        print("\n##############################\n")
        print("# Welcome to {} (version {})\n".format(self.appname, v.__version__))
        print("# {}\n".format(v.__copyright__))
        print("# Date: {}".format(time.strftime("%d-%m-%y %H:%M:%S")))
        print("\n##############################\n")

        self.cli = cli
        self.experimentsFolder = "{}/experiments/".format(rootfolder)
        self.expname = self.getexp(self.experimentsFolder)
        if not isdir('{}/logs'.format(rootfolder)):
            mkdir('{}/logs'.format(rootfolder))

        # Get logger
        self.logger = self.get_logger(rootfolder, self.expname)

        # Get and set configuration
        self.config = Config(rootfolder=rootfolder, expname=self.expname, cli=self.cli)
        self.config.setup()

        self.settings = self.config.settings
        self.folders = self.config.folders
        self.files = self.config.files

        # Create user
        self.user = User(datafolder=self.folders['data'], expname=self.expname,
                         session=self.settings['setup']['session'],
                         demo=self.settings['setup']['demo'],
                         practice=self.settings['setup']['practice'])
        self.user.setup(cli=self.cli)

        self.files['design'] = self.user.designfile

        # Make factorial design
        self.design = Design(expname=self.expname, conditionfile=self.files['conditions'],
                             userfile=self.files['design'], folder=self.folders['expFolder'], custom=custom,
                             demo=self.settings['setup']['demo'], practice=self.settings['setup']['practice'],
                             max_trials=self.settings['setup']['max_trials'])
        self.design.make()

        # Screen
        self.screen = Screen(expfolder=self.folders['expFolder'], expname=self.expname, display_type=self.settings['display']['display_type'],
                             resolution=self.settings['display']['resolution'], size=self.settings['display']['size'],
                             fullscreen=self.settings['display']['fullscreen'], freq=self.settings['display']['freq'],
                             distance=self.settings['display']['distance'], bgcolor=self.settings['display']['bgcolor'])

    def run(self):
        """
        Run and time experiment
        """

        self.logger.logger.info("[{}] --- Start Experiment: '{}' ---".format(__name__, self.expname))

        # Import experiment class from experiment's folder (e.g.: experiments/experiment_name/runtrial.py)
        try:
            sys.path.append(self.folders['expFolder'])
            from runtrial import RunTrial
        except ImportError as e:
            self.logger.logger.fatal('[{}] Could not import RunTrial. Make sure you changed the name of '
                                     '"runtrial_template.py" to "runtrial.py": {}'.format(__name__, e))
            raise e

        # Start timer
        self.startTime = time.time()

        # Open window
        self.screen.open()

        # Instantiate Trial and experiment
        self.trial = Trial(design=self.design, settings=self.settings, userfile=self.user.datafilename,
                           paramsfile=self.files['parameters'], pause_interval=int(self.settings['setup']['pauseInt']))
        runtrial = RunTrial(exp_core=self)

        # Run experiment
        try:
            if self.screen.display_type == 'qt':
                self.screen.ptw.setExperiment(runtrial)
                # Enter main loop (the underscore prevents using the keyword)
                sys.exit(self.screen.QTapp.exec_())
            elif self.screen.display_type == 'psychopy':
                runtrial.run()
        except Exception as e:
            msg = '[{0}] An unexpected error has occurred: {1}'.format(__name__, e)
            self.logger.logger.fatal(msg)
            raise Exception(msg)

        # Stop experiment
        self.stop()

    def stop(self):
        """
        Stop experiment
        """
        if self.screen.display_type == 'psychopy':
            self.screen.close()
        self.stopTime = time.time()

        duration = round((self.stopTime - self.startTime) / 60.0)
        self.logger.logger.info("[{}] End of Experiment '{}'".format(__name__, self.expname))
        self.logger.logger.info("[{0}] Total duration: {1} minutes".format(__name__, duration))
        exit()
