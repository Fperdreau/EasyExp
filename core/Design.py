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
This file is for Design class.
"""

__author__ = "Florian Perdreau"
__copyright__ = "Copyright 2015, Florian Perdreau"
__license__ = "GPL"
__version__ = "0.9.0"
__maintainer__ = "Florian Perdreau"
__email__ = "f.perdreau@donders.ru.nl"
__status__ = "Production"

# IMPORTS
# =======
# Core
from .Config import ConfigFiles

# Import useful libraries
import time
import sys
from os.path import isfile

# Data I/O
import csv

# Numpy
import numpy as np

# Logger
from .system.customlogger import CustomLogger


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
        self.max_trials = max_trials
        self.practice = practice
        self.folder = folder
        self.custom = custom
        self.expname = expname
        self.userfile = userfile
        self.headers = None
        self.conditionFile = ConfigFiles(conditionfile)
        self.demo = demo
        self.dtfName = None
        self.allconditions = {}
        self.conditions = []
        self.factors = []
        self.ntrials = None
        self.design = []

        self.loadConditions()
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
        from .methods.MethodBase import MethodBase
        method_name = "core.methods.{}.{}".format(self.allconditions['method'], self.allconditions['method'])
        try:
            mod = __import__(method_name, fromlist=self.allconditions['method'])
            MethodClass = getattr(mod, self.allconditions['method'])

            self.design, self.conditions = MethodClass.make_design(self.factors, self.allconditions['options'],
                                                                   self.conditions)
        except ImportError as e:
            print('[{}] Could not import "{}": {}'.format(__name__, method_name, e))
            raise e

        # Number of trials
        self.ntrials, nfactors = self.design.shape

        # Make trials list
        self.make_list()

        # Shorten trials list if practice
        if self.practice and self.max_trials is not None and len(self.design) > self.max_trials:
            print('[{}] PRACTICE MODE - Max # of trials: {}'.format(__name__, self.max_trials))
            self.design = self.design[0:self.max_trials]

        # Compute total number of trials for this session
        self.ntrials = len(self.design)
        print('[{}] Total number of trials: {}'.format(__name__, self.ntrials))

        # Randomize trials list
        self.design = self.randomize_list(self.design)

        # Save design into file
        self.save()

    def loadConditions(self):
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

    def fullfact(self, factors, repetition):
        """
        Generates full factorial design
        Parameters
        ----------
        factors: list
        repetition: int - Number of repetitions

        Returns
        -------
        design: 2d-array

        """
        factors = np.array(factors)
        cols = len(factors)
        ssize = np.prod(factors)
        ncycles = ssize
        design = np.zeros((ssize, cols))
        for k in range(cols):
            settings = np.array(range(0, factors[k]))  # settings for kth factor
            nreps = ssize / ncycles  # repeats of consecutive values
            ncycles = ncycles / factors[k]  # repeats of sequence
            settings = np.tile(settings, (nreps, 1))  # repeat each value nreps times
            settings = np.reshape(settings, (1, settings.size), 'F')  # fold into a column
            settings = np.tile(settings, (1, ncycles))  # repeat sequence to fill the array
            design[:, k] = settings[:]

        design = np.tile(design, (repetition, 1))  # Make repetitions
        return design

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
                print('[{}] Importing CUSTOM DESIGN from: {}'.format(__name__, self.folder))
                sys.path.append(self.folder)
                from custom_design import custom_design
            except ImportError as e:
                print('[{}] Could not import custom design'.format(__name__))
                raise e
            design = custom_design(design)

        return design

    def update(self, trialID, data_to_update):
        """
        Update trials info
        :param trialID:
        :param data_to_update:
        :return:
        """
        for trial in self.design:
            if trial['TrialID'] == str(trialID):
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
        except IOError as e:
            print('[{} Could not read "{}"]'.format(__name__, self.userfile))
            raise e
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
                print("[{}] Could not write into the user's datafile: {}".format(__name__, self.userfile))
                raise
            else:
                with open(self.userfile, "wb", 0) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                    writer.writeheader()
                    writer.writerows(self.design)