#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of expFrame
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

# Data I/O
from os.path import isfile
import json
import csv

# Math
import numpy as np


class MethodBase(object):
    """
    Abstract class for methods. Every method implementation should supply the following methods and properties
    - _options - list of default options
    - static make_design() - Generates trials list
    - _get_lists() - Makes responses and intensities lists from data array
    - _load_data() - load data array from file
    - _set_options() - Loads staircase settings from json file
    """

    _options = {
        'nbStairs': 1,
        'nTrials': 40
    }

    _data_file = None
    _settings_file = None
    cur_stair = None
    cpt_stair = 0
    resp_list = None
    int_list = None

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
        raise NotImplementedError("Should have implemented this")

    def _get_lists(self, response=None, intensity=None):
        """
        Makes responses and intensities lists from data array

        Returns
        -------
        void
        """
        if response is None:
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
        else:
            self.resp_list = np.append(self.resp_list, [1 if response == 'True' else 0])
            self.int_list = np.append(self.int_list, intensity)
            self.cpt_stair = len(self.resp_list) - 1

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
            self.data = {}
            print('[{}] User Data filename does not exist yet!'.format(__name__))

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
                import logging
                logging.getLogger('EasyExp').fatal("[{}] The settings file '{}' cannot be found!".format(__name__, self._settings_file))
        return self._options

