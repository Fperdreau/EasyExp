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
This file is for Design class.
"""

# IMPORTS
# =======
# Core
from Config import ConfigFiles

# Import useful libraries
import sys
from os.path import isfile

# Data I/O
import csv

# Logger
import logging


class Design(object):
    """
    This class holds functions used to generate/modify/randomize/save trials list
    :required conditions.json
    """

    ignored_field = {"repetition", "method", "options"}

    def __init__(self, expname='', conditionfile='', userfile='', demo=False, custom=False, folder='', practice=False,
                 max_trials=None):
        """
        Class constructor
        :param bool demo: demo mode (boolean)
        :param string conditionfile: conditions file name
        :param string expname: name of the experiment
        :param string userfile: user design file name
        :param bool practice: practice mode
        :param int max_trials: maximum number of trials in practice mode
        :param bool custom: import custom design
        :param string folder: path to experiment folder (where the custom_design.py lies)
        :return:
        """
        self.max_trials = max_trials  # Maximum number of trials in practice mode
        self.practice = practice  # Enable practice mode (True, False)
        self.folder = folder  # path to experiment folder
        self.custom = custom  # Enable custom experiment design
        self.demo = demo  # Enable demo mode
        self.expname = expname  # Name of the experiment
        self.userfile = userfile  # path to user's file

        # Initialize attributes
        self.headers = None
        self.dtfName = None
        self.allconditions = dict()
        self.conditions = []
        self.factors = []
        self.ntrials = None
        self.design = dict()
        self.method = None

        # Initialize design
        self.conditionFile = ConfigFiles(conditionfile)
        self.load_conditions()
        self.parseconditions()

    def parseconditions(self):
        """
        Computes factors level
        :return void
        """
        for key, val in self.allconditions.iteritems():
            if key != "measures":
                self.conditions.append(key)
                if key not in self.ignored_field:
                    self.factors.append(len(val))

    def make(self):
        """
        This function generates an experimental design based on the factors provided in conditions.json file and write
        it into the design file stored in the participant's folder.
        :return void
        """
        if 'method' not in self.allconditions:
            self.allconditions['method'] = "Constant"

        # Import method implementation
        method_name = "core.methods.{}.{}".format(self.allconditions['method'], self.allconditions['method'])
        try:
            mod = __import__(method_name, fromlist=self.allconditions['method'])
            self.method = getattr(mod, self.allconditions['method'])

            self.design, self.conditions = self.method.make_design(self.factors, self.allconditions['options'],
                                                                   self.conditions)
        except ImportError as e:
            msg = ImportError('[{}] Could not import "{}": {}'.format(__name__, method_name, e))
            logging.getLogger('EasyExp').critical(msg)
            raise msg

        # Number of trials
        self.ntrials, nfactors = self.design.shape

        # Make trials list
        self.make_list()

        # Shorten trials list if practice
        if self.practice and self.max_trials is not None and len(self.design) > self.max_trials:
            logging.getLogger('EasyExp').info('[{}] PRACTICE MODE - Max # of trials: {}'.format(__name__,
                                                                                                self.max_trials))
            self.design = self.design[0:self.max_trials]

        # Compute total number of trials for this session
        self.ntrials = len(self.design)
        logging.getLogger('EasyExp').info('[{}] Total number of trials: {}'.format(__name__, self.ntrials))

        # Randomize trials list
        self.design = self.randomize_list(self.design)

        # Save design into file
        self.save()

    def load_conditions(self):
        """
        Get experimental design from the design file
        """
        self.conditionFile.load()
        self.allconditions = self.conditionFile.data

    def make_list(self):
        """
        Generate a list of dictionaries with one dictionary per trial holding all the trial information.
        """
        new_design = []
        for t in range(self.ntrials):
            trial = {'TrialID': t + 1, 'Replay': True}
            i = 0
            self.headers = ['TrialID', 'Replay']
            for key in self.conditions:
                if key not in self.ignored_field:
                    self.headers.append(key)
                    ind = float(self.design[t, i])
                    if key in ('staircaseID', 'staircaseDir', 'intensity'):
                        trial[key] = int(ind) if key != 'intensity' else ind
                    else:
                        trial[key] = self.allconditions[key][int(ind)]

                    i += 1
            new_design.append(trial)
        self.design = new_design

    def randomize_list(self, design):
        """
        Randomize trials list either using a standard shuffling method or calling a custom randomizing function.
        :param list design: initial trials list. This is actually a list of dictionaries with a dictionary per trial.
        :return list design: randomized trials list
        """
        if not self.custom:
            # Randomize trials
            from random import shuffle
            shuffle(design)
        else:
            # Import custom design if requested
            try:
                logging.getLogger('EasyExp').info('[{}] Importing CUSTOM DESIGN from: {}'.format(__name__, self.folder))
                sys.path.append(self.folder)
                from custom_design import custom_design
            except ImportError:
                msg = ImportError('[{}] Could not import custom design'.format(__name__))
                logging.getLogger('EasyExp').critical(msg)
                raise msg
            design = custom_design(design)

        return design

    def update(self, trial_id, data_to_update):
        """
        Update trials info
        :param trial_id:
        :param data_to_update:
        :return:
        """
        for trial in self.design:
            if trial['TrialID'] == str(trial_id):
                for key, value in data_to_update.iteritems():
                    trial[key] = value

    def get_trial(self, trial_id):
        """
        Get Trial info
        :param trial_id
        :type trial_id int
        :return trial dict
        """
        for trial in self.design:
            if trial['TrialID'] == str(trial_id):
                return trial
        return False

    def load(self):
        """
        Loads experimental design from the design file
        """
        try:
            self.design = []
            with open(self.userfile, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.design.append(row)
        except IOError:
            msg = IOError('[{} Could not read "{}"]'.format(__name__, self.userfile))
            logging.getLogger('EasyExp').critical(msg)
            raise msg
        return self.design

    def save(self, update=False):
        """
        Write experimental design to a file
        :param update overwrite pre-existent design
        :type update bool
        """
        if not isfile(self.userfile) or update:
            try:
                open(self.userfile, "wb", 0)
            except (IOError, TypeError):
                msg = IOError("[{}] Could not write into the user's datafile: {}".format(__name__, self.userfile))
                logging.getLogger('EasyExp').critical(msg)
                raise msg
            else:
                with open(self.userfile, "wb", 0) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                    writer.writeheader()
                    writer.writerows(self.design)
