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

from __future__ import print_function
from __future__ import print_function
import math
import numpy as np

__version__ = "1.1.0"


def deg2pix_old(angle=float, direction=1, distance=550, screen_res=(800, 600), screen_size=(400, 300)):

    """
    Convert visual angle to pixels or pixels to visual angle.
    :param screen_size: Screen size (in mm)
    :type screen_size: tuple
    :param screen_res: Screen resolution (in pixels)
    :type screen_res: tuple
    :param direction: direction of the conversion (1: Visual angle to
     pixels; 2= pixels to visual angle).
    :param angle: size to convert
    :param distance: distance eye-screen in mm
    :return wdth: width expressed in pixels or visual angles.
             hght: height expressed in pixels or visual angles.
     :rtype: tuple (int, int)
    """

    widthscr, heightscr = [float(i) for i in screen_res]
    widthres, heightres = [float(i) for i in screen_size]

    if direction == 1:
        wdth = round(math.tan(deg2rad(angle/2))*2*distance*(widthres/widthscr))
        hght = round(math.tan(deg2rad(angle/2))*2*distance*(heightres/heightscr))
    else:
        wdth = rad2deg(math.atan(((angle/2)/(distance*(widthres/widthscr)))))*2
        hght = rad2deg(math.atan(((angle/2)/(distance*(heightres/heightscr)))))*2

    return int(wdth), int(hght)


def deg2rad(angle):
    """
    Convert degrees to radians
    :param angle: angle to convert (in degree)
    :return: converted angle in radians
    :rtype: float
    """
    return angle*(math.pi/180)


def rad2deg(angle):
    """
    Convert radians to degrees
    :param angle: angle to convert (in radians)
    :return: converted angle in degrees
    :rtype: float
    """
    return float(angle/(math.pi/180))


def cart2pol(x, y):
    """
    Convert cartesian coordinates (x,y) to polar coordinates (rho, theta)
    :param x: horizontal coordinate
    :param y: vertical coordinate
    :return: rho, theta
    :rtype: list (float, float)
    """
    rho = math.sqrt(x**2 + y**2)
    theta = math.atan2(y, x)
    return rho, theta


def pol2cart(rho, phi):
    """
    Converts polar to cartesian
    :param rho: norm
    :param phi: angle
    :return: cartesian coordinates
    :rtype: tuple (float, float)
    """
    x_output = rho * np.cos(phi)
    y_output = rho * np.sin(phi)
    return x_output, y_output


def pix2cm(size, direction, window=None):
    """
    Convert pixels to centimeters or conversely
    :param size: size to convert (pixels or centimeters)
    :param direction: direction of the conversion (1: to cm, 2: to pixels
    :param window: object providing screen's information
    :return: s: converted size
            ppi: pixels per inch
            di: screen diagonal in inches
    :rtype: tuple (float, float, float)
    """
    if window is not None:
        widthscr, heightscr = window.displaySize
        widthres, heightres = window.screensize
    else:
        return False

    i = 2.54  # cm per inch
    wp = widthres
    hp = heightres  # Screen width and height in pixels
    di = round(((math.sqrt((widthscr**2) + (heightscr**2)))/10)/i)  # diagonal in inch
    dp = math.sqrt((wp**2)+(hp**2))  # diagonal in pixels
    ppi = dp/di # pixel per inch

    # Angle: size for converting (in VS), AskedSize(1:pixels, 2:visual angle).
    if direction == 2:  # Cm to Pix
        s = round(size*(ppi/i))
    else:  # Pix to cm
        s = round(size*(i/ppi), -1)

    return s, ppi, di


def roundn(x, n):
    """
    Rounds a value to the nearest multiple of 10^n.
    :param x: number to round
    :param n: requested decimal
    :return: x: rounded value
    :rtype: float
    """
    p = 10**n
    x = p*round(x/p)
    return x


def visdist(d, py, yc, a, window):
    """
    Compute Distance of a particular point on the screen according to the distance from the center of the screen,
    the relative position of the target from this center, and the slant of the screen.
    :param d: distance from eye to screen center
    :param py: horizontal coordinates of the screen center (in pixels from the left border)
    :param yc: vertical coordinates of the screen center (in pixels from the top border)
    :param a: angle (slant) of the screen
    :param window: object providing screen's information
    :return: distance of a point relative to eye.
    :rtype: float
    """
    dy = abs(py - yc)
    dy = pix2cm(dy, 1, window)*10  # in mm
    d1 = math.sin(a)*dy
    ha = math.cos(a)*dy
    angle = math.atan2(d, ha)  # Viewing angle
    d2 = math.cos(angle)*d

    if py - yc > 0:
        d = d2 + d1
    elif py - yc < 0:
        d = d2 - d1
    else:
        d = distance

    return d


def inrect(x, y, rect):
    """
    Test whether input coordinates are inside a given rectangle.
    :param x:
    :param y:
    :param rect: rectangle coordinates (left, top, right, bottom)
    :return: boolean
    :rtype: bool
    """
    rect = [float(r) for r in rect]
    cond1 = (float(x) > rect[0]) & (float(x) < rect[2])
    cond2 = (float(y) > rect[1]) & (float(y) < rect[3])
    return cond1 & cond2


def distance(start, end):
    """
    Compute spherical distance between two given points
    :param start: starting position
    :type start: ndarray
    :param end: end position
    :type end: ndarray
    :return: spherical distance
    :rtype: float
    """
    diff = []
    for key, coord in start:
        diff.append((end[key] - start[key])**2)

    return np.sqrt(np.sum(np.array(diff)))


def pix2deg(size, height, d, resolution):
    """
    Convert pixels to degrees
    :param size: size to convert to degrees (in pixels)
    :param height: screen height (in cm)
    :param d: distance eye-screen (in cm)
    :param resolution: screen vertical resolution (in pixels)
    :return: converted size in degrees
    :rtype: float
    """
    deg_per_px = math.degrees(math.atan2(.5 * height, d)) / (.5 * resolution)
    size_in_deg = size * deg_per_px
    return size_in_deg


def deg2pix(size, height, d, resolution):
    """
    Convert degrees to pixels
    :param size: size to convert to degrees (in pixels)
    :param height: screen height (in cm)
    :param d: distance eye-screen (in cm)
    :param resolution: screen vertical resolution (in pixels)
    :return: converted size in degrees
    :rtype: float
    """
    deg_per_px = math.degrees(math.atan2(.5 * height, d)) / (.5 * resolution)
    size_in_px = size / deg_per_px
    return size_in_px


def deg2m(angle, d):
    """
    This function converts visual angles to meters
    :param float angle: visual angle to convert
    :param float d: distance in meters
    :return float size: converted size in meters
    :rtype: float
    """
    return d * math.tan((math.pi / 180.0) * angle)


def mm2pix(x, y, px, mm):
    """
    Converts millimeters to pixels

    Parameters
    ----------
    :param x: horizontal coordinate (in mm)
    :param y: vertical coordinate (in mm)
    :param px: screen dimension in pixels (width, height)
    :type px: tuple
    :param mm: screen dimension in mm (width, height)
    :type mm: tuple

    Returns
    -------
    :return numpy array (float, float): Converted coordinates
    :rtype: list [float, float]
    """
    pix_density_x = px[0] / mm[0]
    pix_density_y = px[1] / mm[1]
    nx = pix_density_x * x
    ny = pix_density_y * y
    return np.array((float(nx), float(ny)))


def pix2mm(x, y, px, mm):
    """
    Converts pixels to mm

    Parameters
    ----------
    :param x: horizontal coordinate (in pixels)
    :param y: vertical coordinate (in pixels)
    :param px: screen dimension in pixels (width, height)
    :type px: tuple
    :param mm: screen dimension in mm (width, height)
    :type mm: tuple

    Returns
    -------
    :return numpy array (float, float): Converted coordinates
    :rtype: list [float, float]
    """
    pix_density_x = mm[0] / px[0]
    pix_density_y = mm[1] / px[1]
    nx = pix_density_x * x
    ny = pix_density_y * y
    return np.array((float(nx), float(ny)))


def normsize(x, y, width_mm, height_mm):
    """
    Convert mm to normalized units

    Parameters
    ----------
    :param x: size on horizontal axis
    :param y: size on vertical axis
    :param height_mm: screen's height in mm
    :param width_mm: screen's width in mm

    Returns
    -------
    :return: normalized size
    :rtype: list [float, float]

    """
    nx = x / (0.5 * width_mm)
    ny = y / (0.5 * height_mm)
    return np.array((nx, ny))
