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

# Import
from ...com.rusocsci import buttonbox

__version__ = '1.0.0'


class Shutter(object):
    """
    Wrapper class for controlling shutter glasses
    """

    def __init__(self, port="com4"):
        """
        Constructor
        :param port:
        :return:
        """
        try:
            self.link = buttonbox.Buttonbox(port)  # optionally add port="COM17"
            self.open(False, False)
        except Exception as e:
            print(e)

    def open(self, left=False, right=False):
        """
        Open Left and/or Right shutter glasses
        :param left: boolean
        :param right: boolean
        :return:
        """
        try:
            self.link.setLeds([left, right, False, False, False, False, False, False])
        except Exception as e:
            print('Could not open/close shutter glasses: {}'.format(e))
