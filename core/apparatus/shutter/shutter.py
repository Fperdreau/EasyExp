#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau
# Date: 18/01/2015

# Import
from ...com.rusocsci import buttonbox


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
