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

import logging


class MethodContainer(object):
    """
    MethodContainer class
    Handles instances of experiment methods (e.g. staircase) that can be updated independently
    """

    _instances = {}
    _options = None

    def __init__(self, method='PsiMarginal', settings_file=None, data_file=None, options=None):
        """
        MethodContainer constructor

        Parameters
        ----------
        :param options : dictionary providing staircase settings
        :type options: dict
        :param settings_file: full path to settings (json) file
        :type settings_file: str
        :param data_file: full path to data file
        :type data_file: str
        """
        self._method = method
        self._settings_file = settings_file
        self._data_file = data_file
        self.options = options

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, options):
        if self._options is None:
            self._options = dict()
        self._options.update(options)

    def update(self, stair_id, direction, intensity=None, response=None):
        """
        Updates stimulus intensity based on previous response.

        Parameters
        ----------
        :param stair_id: ID of current stair
        :type stair_id: int
        :param direction: direction of current staircase (0: up, 1:down)
        :type direction: int
        :param intensity: list of previously displayed intensities
        :type intensity: str
        :param response: list of previous responses
        :type response: str

        Returns
        -------
        :return intensity: new stimulus intensity
        :rtype intensity: float
        """
        self.__add(stair_id)
        return self._instances[stair_id].update(stair_id=stair_id, direction=direction, intensity=intensity,
                                                response=response)

    def __add(self, id):
        """
        Add method instance
        :param id:
        :return:
        """
        if id not in self._instances:
            method = self.get_method(self._method)
            self._instances[id] = method(settings_file=self._settings_file, data_file=self._data_file,
                                         options=self._options)

    def __remove(self, id):
        """
        Remove method instance
        :param id:
        :return:
        """
        if id in self._instances:
            del self._instances[id]

    @staticmethod
    def get_method(method_name):
        """
        Get method instance
        :param method_name: name of method
        :return:
        """
        # Import method implementation
        method_path = "core.methods.{}.{}".format(method_name, method_name)
        try:
            mod = __import__(method_path, fromlist=method_name)
            return getattr(mod, method_name)
        except ImportError as e:
            msg = ImportError('[{}] Could not import "{}": {}'.format(__name__, method_name, e))
            logging.getLogger('EasyExp').critical(msg)
            raise msg

    @staticmethod
    def make_design(method, factors, options, conditions_name):
        """
        Generates trials list

        Parameters
        ----------
        nb_stairs
        :param method: method name (must match class name)
        :type method: str
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
        design, conditions = MethodContainer.get_method(method_name=method).make_design(factors=factors,
                                                                                        options=options,
                                                                                        conditions_name=conditions_name)
        return design, conditions
