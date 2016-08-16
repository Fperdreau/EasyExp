#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau
# Date: 18/01/2015


class Stimulus(object):
    """

    """

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def update_position(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z