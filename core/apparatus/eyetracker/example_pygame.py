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
from __future__ import print_function
import time
from eyetracker import EyeTracker, Checking
from misc.conversion import deg2pix
from psychopy import event


def stop_exp():
    """
    Exit example if ESCAPE is pressed
    :return:
    """
    allKeys = event.getKeys()
    quit = False
    for thisKey in allKeys:
        if thisKey in ['q', 'escape']:
            quit =True
    return quit


display_type = 'psychopy'  # window's type (pygame, psychopy, qt)
screen_size = 480, 300  # todo construct from psychopy attributes
resolution = 1920, 1080  # Screen resolution
center = 0, 0  # Screen's center in pixels
use_dummy = False  # flag for using dummy mode (mouse simulates eye position)

link = "100.1.1.1"  # Eyetracker IP (100.1.1.1 = localhost)

if display_type is 'psychopy':
    # If we use a psychopy window
    from psychopy import visual, monitors
    # Window
    mon = monitors.Monitor('testMonitor')
    win = visual.Window(
        monitor=mon,
        color=(0, 0, 0),
        pos=(0, 0),
        size=resolution,
        units='pix',
        fullscr=False)
    resolution = win.size
    normRatio = (resolution[1]/float(resolution[0]))
    distance = win.scrDistCM
else:
    raise Exception('Oops. If you want to try out the Qt version, you might use example_Qt.py')

# From this point, the EyeTracker wrapper class works the same whatever we are using a pygame or a psychopy window
eyetracker = EyeTracker(link=link, dummy_mode=use_dummy, sprate=1000, thresvel=35, thresacc=9500, illumi=2,
                        caltype='HV9', dodrift=False, trackedeye='right', display_type=display_type, ptw=win,
                        bgcol=(0, 0, 0), distance=distance, resolution=resolution, winsize=screen_size,
                        inner_tgcol=(0, 0, 0), outer_tgcol=(1, 1, 1), targetsize_out=1.0,
                        targetsize_in=0.25)

# Checking methods (fixationtest, checkfixation)
checking = Checking(eyetracker, eyetracker.display, radius=2)

# Run Eyelink and do a calibration
eyetracker.run()

# Set custom calibration
# ======================
cal_radius = 0.5  # Distance of calibration targets from screen center

# custom 9-points spherical grid
# x, y = eyetracker.calibration.generate_cal_targets(cal_radius, 9, shape='sphere')

# custom 5-points grid
x, y = eyetracker.calibration.generate_cal_targets(cal_radius, 5, shape='rect')

# custom 9-points grid
# x, y = eyetracker.calibration.generate_cal_targets(cal_radius, 9, shape='rect')

# Start calibration
eyetracker.calibration.custom_calibration(x=x, y=y, ctype='HV5')
eyetracker.calibration.calibrate()

# Start trials
stopexp = False
radius_px = deg2pix(size=1.5, height=screen_size[1], distance=distance, resolution=resolution[1])

for trialID in range(5):
    # Starting routine
    eyetracker.start_trial(trialID+1)

    # Test Fixation test
    fix = False
    isfix=False
    while not fix and not stopexp:
        # Test fixation
        fix = checking.fixationtest(opt='fix', isfix=False, fixation_duration=2, time_to_fixate=2, radius=1, rx=200, ry=200)

        # Draw eye position
        eyetracker.eye.draw(flip=False)

        # Get eye position
        eyetracker.eye.get_position()

        # Flip screen
        win.flip()

        stopexp = stop_exp()
        if stopexp:
           break

    print('Fixation test passed')

    # Test fixation validation
    fix = False
    radiusCircle = visual.Circle(win, units='pix', pos=center, radius=checking.radius, fillColor=None)
    while not fix and not stop_exp():
        # Draw radius
        radiusCircle.draw()

        # Draw target
        eyetracker.display.gui.draw_fixation(center[0], center[1], flip=False)

        # Check fixation
        eyetracker.eye.get_position()

        # Draw eye position
        eyetracker.eye.draw(flip=False)

        # Test fixation
        fix = eyetracker.eye.validate(position=[0.5*resolution[0], 0.5*resolution[1]], radius=radius_px, duration=0.200)

        # Flip screen
        win.flip()

        stopexp = stop_exp()
        if stopexp:
            break

    if stopexp:
        break
    print('Fixation validation passed')

    # Start trial
    # Here, we simply draw a black dot at the current gaze location. YAY, our first gaze-contingent experiment!
    trialDuration = 5
    initTime = time.time()
    while time.time() < initTime + trialDuration and not stopexp:
        # Get eye position
        eyetracker.eye.get_position()
        eyeposition = (eyetracker.eye.x, eyetracker.eye.y)

        # Print eye position
        print(eyetracker.eye)

        # Draw eye-position
        eyetracker.eye.draw(flip=False)

        # Flip screen
        win.flip()

        stopexp = stop_exp()
        if stopexp:
            break

    # End the trial (stop recording)
    eyetracker.stop_trial(trial_id=trialID+1)

# Close connection to eyelink
eyetracker.close()

# Close window
win.close()
