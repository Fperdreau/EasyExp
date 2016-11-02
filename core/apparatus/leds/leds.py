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
import serial
import struct

__version__ = '1.0.0'


class Leds(object):
    """
    Wrapper class controlling LEDs' state
    """
    def __init__(self):
        """
        Constructor
        :return:
        """
        try:
            self.link = serial.Serial('/dev/ttyUSB1', 115200)
        except Exception as e:
            print 'LEDS: {}'.format(e)
            self.link = None

        self.state = {}

    def run(self, column=0, row=0):
        """
        Turn on/off a led specified by its row and column position
        :param column:
        :param row:
        :return:
        """
        ind = ','.join((str(column), str(row)))
        if ind not in self.state:
            self.state[ind] = False

        if self.state[ind] is False:
            status = struct.pack('BB', column, row)
            self.state[ind] = True
        else:
            status = struct.pack('BB', column, row+100)
            self.state[ind] = False
        if self.link is not None:
            self.link.write(status)
