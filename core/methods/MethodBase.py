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


class MethodBase(object):
    """
    Abstract class for methods. Every method implementation should supply the following methods and properties
    - _options - list of default options
    - make_design() - Generates trials list
    - _get_lists() - Makes responses and intensities lists from data array
    - _load_data() - load data array from file
    - _set_options() - Loads staircase settings from json file
    """

    _options = {
        'nbStairs': 1,
        'nTrials': 40
    }

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

    def _get_lists(self):
        """
        Makes responses and intensities lists from data array

        Returns
        -------
        void
        """
        raise NotImplementedError("Should have implemented this")

    def _load_data(self):
        """
        Loads data from file

        Returns
        -------
        :return data
        :rtype: 2d-array
        """
        raise NotImplementedError("Should have implemented this")

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
        raise NotImplementedError("Should have implemented this")

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
        raise NotImplementedError("Should have implemented this")

