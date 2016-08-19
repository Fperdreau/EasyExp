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

"""
This file is for Devices class - dependencies container
"""

from __future__ import print_function
import sys
import types

from core.Config import ConfigFiles


class Devices(object):
    """
    Dependency container for devices
    """

    def __init__(self, file_name):
        """
        Devices constructor
        Parameters
        ----------
        file_name
        """
        self.devices = dict()
        self.settingsFile = ConfigFiles(file_name)

    def init(self):
        """
        Instantiate and initialize devices
        Returns
        -------

        """
        self.settingsFile.load()
        for label, params in self.settingsFile.data.iteritems():
            device = Devices.str_to_class(label)
            if label not in self.devices:
                try:
                    self.devices[label] = device(**params)
                except AttributeError:
                    raise AttributeError('Could not instantiate {}'.format(label))

    @staticmethod
    def str_to_class(field):
        """
        Instantiate class from class's name
        Parameters
        ----------
        field: class' name
        :type field: str

        Returns
        -------
        Object
        """
        try:
            identifier = getattr(sys.modules[__name__], field)
        except AttributeError:
            raise NameError("%s doesn't exist." % field)
        if isinstance(identifier, (types.ClassType, types.TypeType)):
            return identifier
        raise TypeError("%s is not a class." % field)