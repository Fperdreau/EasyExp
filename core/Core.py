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

from Devices import Devices

"""
EasyExp is a Python framework designed to ease the implementation of behavioral experiments.
"""

# IMPORTS
# =======
# Version
import version as v

# Core
from Config import Config
from User import User
from Design import Design
from Trial import Trial
from Screen import Screen
from Parameters import Parameters

# Import useful libraries
import time
import sys
from os import listdir, mkdir
from os.path import isdir, join, isfile

# Dialog UI
from gui.gui_wrapper import GuiWrapper

# Logger
from system.customlogger import CustomLogger


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

        # Dependencies
        self.config = None
        self.user = None
        self.trial = None
        self.screen = None
        self.design = None
        self.logger = None
        self.devices = None
        self.parameters = None

        self.__cli = False

        self.folders = {'rootFolder': None, 'data': None, 'expFolder': None}
        self.files = dict()
        self.experimentsFolder = None
        self.status = True
        self.settings = None

        self.startTime = None
        self.stopTime = None

        self.expname = None
        self.exp_version = None

    @staticmethod
    def __get_experiment(folder, cli=False):
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

        if cli:
            selectexp = GuiWrapper.factory(cli, 'nested', data, title='Select Experiment', mandatory=True)
        else:
            selectexp = GuiWrapper.factory(cli, 'nested', data, title='Select Experiment')
        return selectexp.out['Experiment selection']['expname']['value']

    @staticmethod
    def get_logger(rootfolder, expname):
        """
        Get application logger
        :param rootfolder:
        :param expname:
        :return: Logger instance
        :rtype: CustomLogger
        """
        if Core.__logger is None:
            # Set application's logger
            log_file = '{}/logs/{}_{}.log'.format(rootfolder, expname, time.strftime("%d%m%y_%H%M%S"))
            Core.__logger = CustomLogger(Core.appname, file_name=log_file, level='debug')
        return Core.__logger

    def init(self, rootfolder, cli=False, conditions=None):
        """
        Initialize dependencies
        :param string rootfolder: full path to root folder
        :type rootfolder: str
        :param cli: Run in command line (True)
        :type cli: bool
        :param conditions: dictionary providing experiment conditions (to be used instead of conditions.json)
        :type conditions: dict
        """
        # Get experiment
        self.experimentsFolder = "{}/experiments/".format(rootfolder)
        self.expname = self.__get_experiment(self.experimentsFolder, cli=cli)

        # Get logger
        if not isdir('{}/logs'.format(rootfolder)):
            mkdir('{}/logs'.format(rootfolder))
        self.logger = self.get_logger(rootfolder, self.expname)

        # Import experiment
        self.__import_experiment(self.experimentsFolder, self.expname)
        self.exp_version = RunTrial.version if hasattr(RunTrial, 'version') else '1.0.0'

        # Print welcome message
        print("\n##############################\n")
        self.logger.info("# Welcome to {} (version {})".format(self.appname, v.__version__))
        self.logger.info("# {}".format(v.__copyright__))
        self.logger.info("# Date: {}".format(time.strftime("%d-%m-%y %H:%M:%S")))
        self.logger.info("# Experiment: {} (version {})".format(self.expname, self.exp_version))
        print("\n##############################\n")

        # Get and set configuration
        self.config = Config(rootfolder=rootfolder, expname=self.expname,
                             cli=cli)
        self.config.setup()

        self.settings = self.config.settings
        self.folders = self.config.folders
        self.files = self.config.files

        # Get experiment parameters
        self.parameters = Parameters(self.files['parameters'])

        # Create user
        self.user = User(data_folder=self.folders['data'], expname='{}_v{}'.format(
            self.expname, self.exp_version.replace('.', '-')), **self.__filter_args(User, self.settings['setup']))
        self.user.setup(cli=cli)

        self.files['design'] = self.user.designfile

        # Make factorial design
        self.design = Design(conditionfile=self.files['conditions'], userfile=self.files['design'],
                             folder=self.folders['expFolder'], conditions=conditions,
                             **self.__filter_args(Design, self.settings['setup']))
        self.design.make()

        # Devices
        self.devices = Devices(exp_folder=self.folders['expFolder'], base_name=self.user.dftName, cli=cli)

        # Screen
        self.screen = Screen(expfolder=self.folders['expFolder'], expname=self.expname,
                             **self.__filter_args(Screen, self.settings['display']))

    @staticmethod
    def __filter_args(class_obj, args):
        """
        Filter arguments passed to class constructor
        :param class_obj: class instance
        :param args: arguments
        :return: filtered dictionary
        :rtype: dict
        """
        import inspect
        this_args = inspect.getargspec(class_obj.__init__)
        new_dict = dict()
        for a in this_args[0]:
            if a is not "self" and a in args:
                new_dict.update({a: args[a]})
        return new_dict

    def __import_experiment(self, exp_folder, exp_name):
        """
        # Import experiment class from experiment's folder (e.g.: experiments/experiment_name/runtrial.py)
        :param exp_folder: path to experiments folder
        :param exp_name: experiment name
        :return: void
        """
        try:
            sys.path.append(join(exp_folder, exp_name))
            global RunTrial
            from runtrial import RunTrial

        except ImportError as e:
            msg = '[{}] Could not import RunTrial. Make sure you changed the name of '"runtrial_template.py"' ' \
                  'to "runtrial.py": {}'.format(__name__, e)
            self.logger.fatal(msg)
            raise RuntimeError(msg)

    def run(self):
        """
        Run and time experiment
        """
        self.logger.info("[{}] --- Start Experiment: '{}' ---".format(__name__, self.expname, self.exp_version))

        # Start timer
        self.startTime = time.time()

        # Open window
        self.screen.open()

        # Instantiate Trial and experiment
        self.trial = Trial(design=self.design, settings=self.settings, userfile=self.user.datafilename,
                           pause_interval=int(self.settings['setup']['pauseInt']))
        runtrial = RunTrial(exp_core=self)

        # Run experiment
        try:
            if self.screen.display_type == 'qt':
                self.screen.ptw.setExperiment(runtrial)
                # Enter main loop (the underscore prevents using the keyword)
                sys.exit(self.screen.QTapp.exec_())
            elif self.screen.display_type == 'psychopy':
                runtrial.run()
        except (KeyboardInterrupt, SystemExit) as e:
            msg = '[{0}] Exit requested: {1}'.format(__name__, e)
            self.logger.exception(msg)

            # Quit experiment and close all devices
            runtrial.quit()
        except (RuntimeError, Exception) as e:
            msg = '[{0}] An unexpected error has occurred: {1}'.format(__name__, e)
            self.logger.exception(msg)

            # Quit experiment and close all devices
            runtrial.quit()
            
            raise Exception(msg)
        finally:
            # Stop experiment
            self.stop()

            # run callback script
            self.run_callback()

            # End
            exit()

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

    def run_callback(self):
        """
        Run callback script
        :return: 
        """
        filename = join(self.experimentsFolder, self.expname, 'callback.py')
        if isfile(filename):
            try:
                sys.path.insert(0, join(self.experimentsFolder, self.expname))
                import callback

            except ImportError as e:
                msg = '[{}] Error while executing callback script [path: {}]: {}'.format(__name__, filename, e)
                self.logger.fatal(msg)
                raise RuntimeError(msg)


