#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import numpy as np
from os.path import isfile

# Import Base class
from ..MethodBase import MethodBase

# Data I/O
import json
import csv

__author__ = "Florian Perdreau"
__copyright__ = "Copyright 2015, Florian Perdreau"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Florian Perdreau"
__email__ = "f.perdreau@donders.ru.nl"
__status__ = "Production"


class StaircaseASA(MethodBase):
    """
    Adaptive staircase -- accelerated stochastic approximation

    The accelerated stochastic approximation is a non-parametric adaptive
    method to find rapidly a threshold. it was described by Kesten (1958).
    this program is an example of its use with two interleaved methods.

    References
    Kesten, H. (1958). Accelerated Stochastic Approximation. The Annals of Mathematical Statistics, 29, 1, 41-59.

    Usage
    -----
    Staircase trials list can be generated using StairCaseASA.make_design() method. It is typically called by
    ExpCore.Design class, which loads conditions from the conditions file located in the experiment folder.

    # Example of design dictionary
    design = ({'trialID': 1, 'staircaseID': 1, 'staircaseDir': 0, 'condition1': 'left'},
             {'trialID': 2, 'staircaseID': 2, 'staircaseDir': 1, 'condition1': 'right'},
             ...
             {'trialID': 180, 'staircaseID': 1, 'staircaseDir': 0, 'condition1': 'right'})

    path_to_conditions_file = 'some/path/to/file/conditions.json'
    path_to_data_file = 'some/path/to/file/my_data.csv'

    # Instantiate staircase (if "options" dictionary is not passed as argument to the constructor, then options are
    # loaded from conditions file)
    myStairCase = StaircaseASA(settings_file=path_to_conditions_file, data_file=path_to_data_file)

    # Loop over trials
    for trial in design:
         myStairCase.update(stair_id=trial['staircaseID'], direction=trial['staircaseDir'])
         print(myStairCase.intensity)

    """

    # Default options
    _options = {
        'stimRange': [0, 1],            # Boundaries of stimulus range
        'maxInitialStepSize': 0.4,      # Size of initial step (for faster convergence, it should be half of the range)
        'stoppingStep': 0.1,            # Convergence criterion
        'threshold': 0.75,              # Desired threshold
        'nTrials': 40,                  # Number of trials per staircase
        'limits': False,                # Constraints picked intensity to fall within the initial range
        'nbStairs': 1,                  # Number of staircase per condition
        "warm_up": 4,                   # Number of warm-up trials per staircase (only extremes intensity)
        "response_field": "response",   # Name of response field in data file
        "intensity_field": "intensity"  # Name of intensity field in data file
    }

    def __init__(self, settings_file=None, data_file=None, options=None):
        """
        StairCaseASA constructor

        Parameters
        ----------
        :param options : dictionary providing staircase settings
        :type options: dict
        :param settings_file: full path to settings (json) file
        :type settings_file: str
        :param data_file: full path to data file
        :type data_file: str
        """

        self._settings_file = settings_file
        self._data_file = data_file

        # Load staircase settings from file
        self._load_options(options)

        self.Done = False
        self.cur_stair = 1
        self.intensity = None

        # Initialize arrays
        self.resp_list = np.zeros((1, self._options['nTrials']))
        self.int_list = np.zeros((1, self._options['nTrials']))
        self.StairProgress = 0
        self.cpt_stair = 0
        self.data = []

    @staticmethod
    def make_design(factors, options, conditions_name):
        """
        Generates trials list

        Parameters
        ----------
        nb_stairs
        :param factors: list of numbers of levels per factor
        :type factors: array-like
        :param options: Staircase options
        :type options: dict
        :param conditions_name: list of conditions (columns) name
        :type conditions_name: list

        Returns
        -------
        :return design: trials list (trials x conditions)
        :rtype design: ndarray
        :return conditions_name: updated list of conditions name
        :rtype conditions_name: list
        """
        factors.append(int(options['nbStairs']))

        factors = np.array(factors)  # Convert to numpy array
        cols = len(factors)  # Number of columns (factors)
        ssize = np.prod(factors)  # Total number of conditions
        ncycles = ssize
        design = np.zeros((ssize, cols + 1))
        for k in range(cols):
            settings = np.array(range(0, factors[k]))  # settings for kth factor
            nreps = ssize / ncycles  # repeats of consecutive values
            ncycles = ncycles / factors[k]  # repeats of sequence
            settings = np.tile(settings, (nreps, 1))  # repeat each value nreps times
            settings = np.reshape(settings, (1, settings.size), 'F')  # fold into a column
            settings = np.tile(settings, (1, ncycles))  # repeat sequence to fill the array
            design[:, k] = settings[:]

        nb_all_stairs = np.prod(factors)
        design[:, cols] = range(nb_all_stairs)  # Add methods' IDs

        design = np.tile(design, (options['nTrials'], 1))  # Make repetitions

        # Update list of conditions names
        conditions_name.append('staircaseDir')
        conditions_name.append('staircaseID')

        return design, conditions_name

    def compute(self):
        """
        Compute new intensity
        :return:
        """
        # Compute new intensity
        # number of intensities displayed so far (including current, excluding warm-up)
        nn = self.cpt_stair - self._options['warm_up']
        int_curr = self.int_list[-1]  # current intensity being displayed
        cc = self._options['maxInitialStepSize'] / max(self._options['threshold'], 1 - self._options['threshold'])
        mm = 0  # number of shifts in response categories
        resp_prev = self.resp_list[self._options['warm_up']]
        for ii in range(self._options['warm_up'], nn):
            resp_curr = self.resp_list[ii]
            if resp_curr != resp_prev:
                mm += 1
            resp_prev = resp_curr

        resp_curr = self.resp_list[-1]

        if nn <= 2:
            step = (cc / nn) * (resp_curr - self._options['threshold'])
        else:
            step = (cc / (2 + mm)) * (resp_curr - self._options['threshold'])

        int_next = int_curr - step
        lim = False
        if self._options['limits']:
            if int_next <= self._options['stimRange'][0]:
                lim = True
                int_next = self._options['stimRange'][0]
            elif int_next >= self._options['stimRange'][1]:
                lim = True
                int_next = self._options['stimRange'][1]

        # Staircase progression
        self.Done = False
        if not self._options['stoppingStep'] and not lim:
            self.Done = (abs(int_next - int_curr) < self._options['stoppingStep']) \
                        or self.cpt_stair == self._options['nTrials']

        self.intensity = int_next
        return self.intensity