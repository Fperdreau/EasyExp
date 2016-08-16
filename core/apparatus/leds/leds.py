#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau
# Date: 18/01/2015

# Import
import serial
import struct


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
