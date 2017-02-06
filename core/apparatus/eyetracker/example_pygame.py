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

# Imports
import time
import pygame
from pygame.constants import *
import numpy as np
from eyetracker import EyeTracker, Checking, deg2pix


def normalize(x_input, y_input, resolution):
    """
    Normalize coordinates to Psychopy coordinate system (0,0 = screen center)
    :param float x_input:
    :param float y_input:
    :param tuple resolution: window resolution in pixels
    :return:
    """
    x_output = (x_input - 0.5*resolution[0])/(0.5*resolution[0])
    y_output = (0.5*resolution[1]-y_input)/(0.5*resolution[1])
    return x_output, y_output


def cart2pol(x_input, y_input):
    """
    Converts cartesian to polar coordinates
    Parameters
    ----------
    x_input
    y_input

    Returns
    -------

    """
    rho = np.sqrt(x_input**2 + y_input**2)
    phi = np.arctan2(y_input, x_input)
    return rho, phi


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

display_type = 'psychopy'  # window's type (pygame, psychopy, qt)
resolution = 1680, 1050  # Screen resolution
screen_size = 400, 300
distance = 550  # Distance eye-screen (in mm)
center = 0, 0  # Screen's center in pixels
normCenter = np.array(center, dtype='float32')/np.array(resolution, dtype='float32')  # Normalized screen's center

link = "100.1.1.1"  # Eyetracker IP (100.1.1.1 = localhost)

if display_type is 'psychopy':
    # If we use a psychopy window
    from psychopy import visual
    # Window
    win = visual.Window(
        size=resolution,
        monitor='TestMonitor',
        color=(-1, -1, -1),
        pos=(0, 0),
        units='pix',
        winType='pygame',
        fullscr=True)

elif display_type is 'pygame':
    # If we use a pygame window
    # Initialize and open a Pygame window
    pygame.init()
    pygame.display.init()
    pygame.mixer.init()
    pygame.display.set_mode(resolution, DOUBLEBUF | RLEACCEL, 32)
    pygame.mouse.set_visible(False)
    win = pygame.display  # Pointer to the pygame windows
else:
    raise Exception('Oops. If you want to try out the Qt version, you might use example_Qt.py')

# From this point, the EyeTracker wrapper class works the same whatever we are using a pygame or a psychopy window
eyetracker = EyeTracker(link=link, dummy_mode=False, sprate=1000, thresvel=35, thresacc=9500, illumi=2,
                        caltype='HV9', dodrift=False, trackedeye='left', display_type=display_type, ptw=win,
                        bgcol=(0, 0, 0), distance=distance, resolution=resolution, winsize=screen_size,
                        inner_tgcol=(0, 0, 0), outer_tgcol=(1, 1, 1), targetsize_out=1.0,
                        targetsize_in=0.25)

# Checking methods (fixationtest, checkfixation)
checking = Checking(eyetracker, eyetracker.display, radius=1.5)

# Run Eyelink and do a calibration
eyetracker.run()

# Set custom calibration
# Create calibration points (polar grid, with points spaced by 45 degrees)
x, y = pol2cart(0.25*(resolution[0]/2), np.linspace(0, 2*np.pi, 9))
x += 0.5*resolution[0]  # Center coordinates on screen center
y += 0.5*resolution[1]

# Start calibration
eyetracker.calibration.custom_calibration(x=x, y=y, ctype='HV9')
eyetracker.calibration.calibrate()

# Start trials
stopexp = False
for trialID in range(5):
    # Starting routine
    eyetracker.start_trial(trialID+1)

    # Fixation test before we start the trial
    fix = False
    while not fix and not stopexp:
        # Draw radius
        radiusCircle = visual.Circle(win, units='pix', pos=normCenter, radius=checking.radius, fillColor=None)
        radiusCircle.draw()

        # Draw target
        eyetracker.display.gui.draw_fixation(normCenter[0], normCenter[1], flip=False)

        # Draw eye-position
        eyetracker.display.gui.draw_eye(x=eyetracker.eye.x - 0.5*resolution[0],
                                        y=-eyetracker.eye.y + 0.5*resolution[1], flip=False)

        # Check fixation
        fix = checking.fixationcheck(cx=0.5*resolution[0], cy=0.5*resolution[1])
        print(eyetracker.eye)

        # Flip screen
        win.flip()

        # Exit example if ESCAPE is pressed
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        stopexp = keys[pygame.K_ESCAPE]
        if stopexp:
            break

    print('Fixated: {}'.format(fix))

    # Start trial
    # Here, we simply draw a black dot at the current gaze location. YAY, our first gaze-contingent experiment!
    trialDuration = 5
    initTime = time.time()
    while time.time() < initTime + trialDuration and not stopexp:
        # Get eye position
        eyetracker.eyes['left'].get_position()
        eyeposition = (eyetracker.eye.x, eyetracker.eye.y)
        print(eyetracker.eye)

        # Draw eye-position
        eyetracker.display.gui.draw_eye(x=eyetracker.eye.x - 0.5*resolution[0],
                                        y=-eyetracker.eye.y + 0.5*resolution[1], flip=False)

        win.flip()

        # Exit example if ESCAPE is pressed
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        stopexp = keys[pygame.K_ESCAPE]

    # End the trial (stop recording)
    eyetracker.stop_trial()

    if stopexp:
        break

# Close connection to eyelink
eyetracker.close()

# Close window
win.close()
