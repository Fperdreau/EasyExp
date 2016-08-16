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


class Constant(MethodBase):
    """
    Constant stimuli

    Usage
    -----
    Trial and intensities list can be generated using Random.make_design() method. It is typically called by
    ExpCore.Design class, which loads conditions from the conditions file located in the experiment folder.

    # Example of trials list dictionary
    design = {{'trialID': 1, 'staircaseID': 1, 'staircaseDir': 0, 'condition1': 'left'},
             {'trialID': 2, 'staircaseID': 2, 'staircaseDir': 1, 'condition1': 'right'},
            ...
            {'trialID': 180, 'staircaseID': 1, 'staircaseDir': 0, 'condition1': 'right'},}

    # Implementation
    path_to_conditions_file = 'some/path/to/file/conditions.json'
    path_to_data_file = 'some/path/to/file/my_data.csv'
    factors = [2, 3]

    # Default options
    options = {
        'repetition': 25,            # Number of trials per stimulus intensity
        "response_field": "response",   # Name of response field in data file
        "intensity_field": "intensity"  # Name of intensity field in data file
    }
    design = Random.make_design(factors, options)
    for t in design:
        print(t)
    """

    # Default options
    _options = {
        'repetition': 30,                # Number of decimals
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

        design = np.tile(design, (options['repetition'], 1))  # Make repetitions

        return design, conditions_name

    def update(self, stair_id, intensities=None, responses=None):
        """
        Updates stimulus intensity based on previous response.

        Parameters
        ----------
        :param stair_id: ID of current stair
        :type stair_id: int
        :param intensities: list of previously displayed intensities
        :type intensities: array-like
        :param responses: list of previous responses
        :type responses: array-like

        Returns
        -------
        :return intensity: new stimulus intensity
        :rtype intensity: float
        """
        pass

    def _get_lists(self):
        """
        Makes responses and intensities lists from data array

        Returns
        -------
        void
        """
        resp_list = np.zeros((1, self._options['nTrials']))
        int_list = np.zeros((1, self._options['nTrials']))

        cpt_stair = 0
        for trial in self.data:
            if trial['Replay'] == "False" and int(trial['staircaseID']) == self.cur_stair:
                resp_list[0, cpt_stair] = 1 if trial[self._options['response_field']] == 'True' else 0
                int_list[0, cpt_stair] = float(trial[self._options['intensity_field']])
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


def _test():
    from pprint import pprint

    factors = [2, 3]  # List of factors levels

    # Default options
    options = {
        'stimRange': [-3, 3],  # Boundaries of stimulus range
        'resolution': 2,  # Number of decimals
        'nTrials': 10,  # Number of trials per condition
        "response_field": "response",  # Name of response field in data file
        "intensity_field": "intensity"  # Name of intensity field in data file
    }
    design = Constant.make_design(factors, options)
    pprint(design)

if __name__ == '__main__':
    _test()
