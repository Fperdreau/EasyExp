#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau (f.perdreau@donders.ru.nl)
# Date: 15/03/2015

import math
import numpy as np


def deg2pix(angle=float, direction=1, distance=550, screen_res=(800, 600), screen_size=(400, 300)):

    """
    Convert visual angle to pixels or pixels to visual angle.
    :param direction: direction of the conversion (1: Visual angle to
     pixels; 2= pixels to visual angle).
    :param angle: size to convert
    :param distance: distance eye-screen in mm
    :param window: object providing screen's information
    :return: wdth: width expressed in pixels or visual angles.
             hght: height expressed in pixels or visual angles.
    """

    widthscr, heightscr = [float(i) for i in screen_res]
    widthres, heightres = [float(i) for i in screen_size]

    if direction == 1:
        wdth = round(math.tan(deg2rad(angle/2))*2*distance*(widthres/widthscr))
        hght = round(math.tan(deg2rad(angle/2))*2*distance*(heightres/heightscr))
    else:
        wdth = rad2deg(math.atan(((angle/2)/(distance*(widthres/widthscr)))))*2
        hght = rad2deg(math.atan(((angle/2)/(distance*(heightres/heightscr)))))*2

    print 'Resolution: {}, Size: {}'.format(screen_res,screen_size)
    print 'Angle to convert: {}, returned: {}'.format(angle, wdth)
    return int(wdth)


def deg2rad(angle):

    """
    Convert degrees to radians
    :param angle: angle to convert (in degree)
    :return: converted angle in radians
    """
    return (angle*(math.pi/180))


def rad2deg(angle):

    """
    Convert radians to degrees
    :param angle: angle to convert (in radians)
    :return: converted angle in degrees
    """
    return float(angle/(math.pi/180))


def cart2pol(x, y):

    """
    Convert cartesian coordinates (x,y) to polar coordinates (rho, theta)
    :param x:
    :param y:
    :return: rho, theta
    """
    rho = math.sqrt(x**2 + y**2)
    theta = math.atan2(y, x)
    return rho, theta


def pol2cart(rho, phi):
    """
    Converts polar to cartesian
    Parameters
    ----------
    rho
    phi

    Returns
    -------

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
    :param x:
    :param n:
    :return: x: rounded value
    """
    p = 10**n
    x = p*round(x/p)
    return x


def visdist(distance, py, yc, a, window):

    """
    Compute Distance of a particular point on the screen according to the distance from the center of the screen,
    the relative position of the target from this center, and the slant of the screen.
    :param distance:
    :param py: horizontal coordinates of the screen center (in pixels from the left border)
    :param yc: vertical coordinates of the screen center (in pixels from the top border)
    :param a: angle (slant) of the screen
    :param window: object providing screen's information
    :return:
    """
    dy = abs(py - yc)
    dy = pix2cm(dy, 1, window)*10  # in mm
    d1 = math.sin(a)*dy
    ha = math.cos(a)*dy
    angle = math.atan2(distance, ha)  # Viewing angle
    d2 = math.cos(angle)*distance

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
    """
    cond1 = x > rect[1] & x < rect[3]
    cond2 = y > rect[2] & y < rect[4]
    return cond1 & cond2


def deg2m(angle, d):
    """
    This function converts visual angles to meters
    :param float angle: visual angle to convert
    :param float d: distance in meters
    :return float size: converted size in meters
    """
    import math
    return d * math.tan((math.pi / 180.0) * angle)


def mm2pix(x, y, px, mm):
    """
    Converts millimeters to pixels

    Parameters
    ----------
    :param x: horizontal coordinate
    :param y: vertical coordinate
    :param px: screen dimension in pixels (width, height)
    :type px: tuple
    :param mm: screen dimension in mm (width, height)
    :type mm: tuple

    Returns
    -------
    :return numpy array (int, int): Converted coordinates
    """
    pix_density_x = px[0] / mm[0]
    pix_density_y = px[1] / mm[1]
    nx = pix_density_x * x
    ny = pix_density_y * y
    return np.array((int(nx), int(ny)))


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

    """
    nx = x / (0.5 * width_mm)
    ny = y / (0.5 * height_mm)
    return np.array((nx, ny))
