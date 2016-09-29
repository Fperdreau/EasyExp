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

    >>># Example of design dictionary
    >>>design = {{'trialID': 1, 'staircaseID': 1, 'staircaseDir': 0, 'condition1': 'left'},
    >>>         {'trialID': 2, 'staircaseID': 2, 'staircaseDir': 1, 'condition1': 'right'},
    >>>         ...
    >>>         {'trialID': 180, 'staircaseID': 1, 'staircaseDir': 0, 'condition1': 'right'},}

    >>>path_to_conditions_file = 'some/path/to/file/conditions.json'
    >>>path_to_data_file = 'some/path/to/file/my_data.csv'

    >>># Instantiate staircase (if "options" dictionary is not passed as argument to the constructor, then options are
    >>># loaded from conditions file)
    >>>myStairCase = StaircaseASA(settings_file=path_to_conditions_file, data_file=path_to_data_file)

    >>># Loop over trials
    >>>for trial in design:
    >>>     myStairCase.update(stair_id=trial['staircaseID'], direction=trial['staircaseDir'])
    >>>     print(myStairCase.intensity)

    """

    # Default options
    _options = {
        'stimRange': [0, 1],            # Boundaries of stimulus range
        'maxInitialStepSize': 0.4,      # Size of initial step
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

    def update(self, stair_id, direction, intensities=None, responses=None):
        """
        Updates stimulus intensity based on previous response.

        Parameters
        ----------
        :param stair_id: ID of current stair
        :type stair_id: int
        :param direction: direction of current staircase (0: up, 1:down)
        :type direction: int
        :param intensities: list of previously displayed intensities
        :type intensities: array-like
        :param responses: list of previous responses
        :type responses: array-like

        Returns
        -------
        :return intensity: new stimulus intensity
        :rtype intensity: float
        """
        self.cur_stair = stair_id

        # First, we make response and intensity lists from data
        if intensities is None:
            self._load_data()
            self._get_lists()
        else:
            self.int_list = intensities
            self.resp_list = responses
            self.cpt_stair = len(intensities)

        if self.cpt_stair < self._options['warm_up']:
            # If warm-up phase, then present extremes values
            self.intensity = self._options['stimRange'][self.cpt_stair % 2]
            return self.intensity
        elif self.cpt_stair == self._options['warm_up']:
            # If this is the first trial for the current staircase, then returns initial intensity
            self.intensity = self._options['stimRange'][direction]
            return self.intensity

        # Compute new intensity
        # number of intensities displayed so far (including current, excluding warm-up)
        nn = self.cpt_stair - self._options['warm_up']
        int_curr = self.int_list[0, nn-1]  # current intensity being displayed
        cc = self._options['maxInitialStepSize'] / max(self._options['threshold'],
                                                       1 - self._options['threshold'])
        mm = 0  # number of shifts in response categories
        resp_prev = self.resp_list[0, 0]
        for ii in range(1, nn-1):
            resp_curr = self.resp_list[0, ii]
            if resp_curr != resp_prev:
                mm += 1
            resp_prev = resp_curr

        resp_curr = self.resp_list[0, nn-1]

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

    def _get_lists(self):
        """
        Makes responses and intensities lists from data array (excluding warm-up trials)

        Returns
        -------
        void
        """
        resp_list = np.zeros((1, self._options['nTrials'] - self._options['warm_up']))
        int_list = np.zeros((1, self._options['nTrials'] - self._options['warm_up']))

        cpt_stair = 0
        t = 0
        for trial in self.data:
            if trial['Replay'] == "False" and int(trial['staircaseID']) == self.cur_stair:
                # Only store previous responses and intensities if warm-up is over
                if cpt_stair >= self._options['warm_up']:
                    resp_list[0, t] = 1 if trial[self._options['response_field']] == 'True' else 0
                    int_list[0, t] = float(trial[self._options['intensity_field']])
                    t += 1

                cpt_stair += 1
        self.cpt_stair = cpt_stair
        self.resp_list = resp_list
        self.int_list = int_list

    def _load_data(self):
        """
        Loads data from file

        Returns
        -------
        :return data
        :rtype: 2d-array
        """
        data = []
        try:
            with open(self._data_file) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            self.data = data
        except (IOError, TypeError):
            print('[StairCaseASA] User Data filename does not exist yet!')

    def _set_options(self, options):
        """

        Parameters
        ----------
        :param options: dictionary providing staircase settings
        :type options: dict

        Returns
        -------
        void
        """
        for prop, value in options.iteritems():
            self._options[prop] = value

    def _load_options(self, options=None):
        """
        Loads staircase settings from json file

        Parameters
        ----------
        :param options: dictionary providing staircase settings
        :type options: dict

        Returns
        -------
        :return _options: dictionary providing staircase's settings
        :rtype _options: dict
        """
        if options is not None:
            self._set_options(options)
        else:
            # Read from file
            if isfile(self._settings_file):
                json_info = open(self._settings_file, 'r')
                data = json.load(json_info)
                self._set_options(data['options'])
                json_info.close()
            else:
                print("[StairCaseASA] The settings file '{}' cannot be found!".format(self._settings_file))
        return self._options
