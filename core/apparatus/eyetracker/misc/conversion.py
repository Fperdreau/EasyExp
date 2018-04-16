#!/usr/bin/python
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

import math
import numpy as np


def deg2pix(size, height, distance, resolution):
    """
    Convert degrees to pixels
    :param size: size to convert to degrees (in pixels)
    :param height: screen height (in cm)
    :param distance: distance eye-screen (in cm)
    :param resolution: screen vertical resolution (in pixels)
    :return: converted size in degrees
    """
    deg_per_px = math.degrees(math.atan2(.5 * height, distance)) / (.5 * resolution)
    size_in_px = size / deg_per_px
    return size_in_px


def deg2rad(angle):
    """
    Convert degrees to radians
    :param angle: angle to convert (in degree)
    :type angle: float

    :return: converted angle in radians
    """
    return float(angle*(math.pi/180))


def rad2deg(angle):
    """
    Convert radians to degrees
    :param angle: angle to convert (in radians)
    :type angle: float

    :return: converted angle in degrees
    """
    return float(angle/(math.pi/180))


def el2Screen(pos, displaySize, sizeX, toEl=False):
    """
    Maps mouse position to Eyelink coordinates
    :param pos: position in original coordinates
    :type pos: list
    :param toEl: True(map screen coordinates to Eyelink from psychopy), False (map Eyelink to psychopy)
    :type toEl: bool
    :return: updatePos: updated coordinates
    :rtype: list
    """
    updatedPos = np.empty(2)
    if toEl:
        updatedPos[0] = pos[0] + 0.5*sizeX
        updatedPos[1] = (displaySize[1] * 0.5) - pos[1]
    else:
        updatedPos[0] = pos[0] - displaySize[0] * 0.5
        updatedPos[1] = -(pos[1] - displaySize[1] * 0.5)
    return updatedPos