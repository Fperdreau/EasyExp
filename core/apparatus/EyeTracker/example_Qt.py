#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of EasyExp
#
# Copyright (C) 2015 Florian Perdreau, Radboud University Nijmegen
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

# Example with QT application
import sys
from PyQt4 import QtCore, QtGui
from eyetracker import EyeTracker

# General graphical settings
display_type = 'qt'  # window's type (pygame, psychopy, qt)
resolution = 1680, 1050  # Screen resolution

# Eyetracker IP (100.1.1.1 = localhost)
link = "100.1.1.1"

# Initialize QT application
app = QtGui.QApplication(sys.argv)

# Initialize Tracker
eyetracker = EyeTracker(link=link, dummy_mode=False, sprate=1000, thresvel=35, thresacc=9500, illumi=2,
                        caltype='HV5', dodrift=False, trackedeye='right', display_type=display_type, ptw=app,
                        bgcol=(127, 127, 127), distance=550, resolution=resolution, winsize=(400, 300),
                        inner_tgcol=(127, 127, 127), outer_tgcol=(255, 255, 255), targetsize_out=1.5,
                        targetsize_in=0.5)

app.lastWindowClosed.connect(QtCore.QCoreApplication.instance().quit)

# Show application
eyetracker.display.gui.show()

# Start calibration
eyetracker.calibration.calibrate()

# End of runtime
sys.exit(app.exec_())
