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

# IMPORTS
# =======
# Import useful libraries
import sys

# Logger
import logging


class Screen(object):
    """
    Create a useful object providing information about the window
    """

    allowed_displays = ['psychopy', 'pygame', 'qt']

    def __init__(self, expname='', expfolder='', display_type='pygame', resolution=(1920, 1080), size=(400, 300),
                 fullscreen=False, freq=60.0, distance=550, bgcolor=(0, 0, 0)):
        """
        Class constructor
        :param expname: Experiment's name
        :param expfolder: Experiment's folder
        :param display_type: window's type ("qt", "psychopy")
        :param resolution: screen's resolution (in pixels)
        :param size: screen's size (in mm)
        :param fullscreen: open fullscreen window (False/True)
        :param freq: screen's refresh rate (in Hz)
        :param distance: distance eyes/screen's surface
        :param bgcolor: screen's default background color
        :return:
        """
        self.expname = expname
        self.expfolder = expfolder
        self.resolution = resolution
        self.size = size
        self.freq = freq
        self.distance = distance
        self.fullscreen = fullscreen
        self.bgcolor = bgcolor

        # Set display type
        if display_type not in Screen.allowed_displays:
            msg = Exception('[{}] "{}" is not a valid display type'.format(__name__, display_type))
            logging.getLogger('EasyExp').critical(msg)
        self.display_type = display_type

        self.scrRes = None
        self.ptw = None

        self.width_px = self.resolution[0]
        self.height_px = self.resolution[1]
        self.height_mm = self.size[1]
        self.width_mm = self.size[0]

        # Get screen resolution
        self.getScrRes()
        logging.getLogger('EasyExp').info(self)

    def __str__(self):
        """
        Print screen's information
        :return:
        """
        return '\n--- Display settings ---\n' \
               '\tType: {0}\n' \
               '\tResolution (requested, pixels): {1}\n' \
               '\tResolution (native, pixels): {2}\n' \
               '\tSize (mm): {3}\n' \
               '\tRefresh rate (Hz): {4}\n' \
               '\tDistance (mm): {5}\n' \
            .format(self.display_type, self.resolution, self.scrRes, self.size, self.freq, self.distance)

    def open(self):
        """
        Create and open a window (Qt or pygame)
        :return:
        """
        try:
            if self.display_type == 'qt':
                # Dialog UI
                import signal
                from display.qtwindow import QtWindow

                # PyQt (package python-qt4-gl on Ubuntu)
                from PyQt4.QtGui import QApplication

                # Build Qt application
                sys.path.append(self.expfolder)
                self.QTapp = QApplication(sys.argv)
                self.QTapp.setApplicationName(self.expname)

                # Windows pointer
                self.ptw = QtWindow(self)
                self.QTapp.lastWindowClosed.connect(self.ptw.quit)  # make upper right cross work
                signal.signal(signal.SIGINT, self.ptw.quit)  # make ctrl-c work
            elif self.display_type == 'psychopy':
                from psychopy import visual
                self.ptw = visual.Window(
                    size=(self.width_px, self.height_px),
                    color=self.bgcolor,
                    units='pix',
                    winType='pygame',
                    pos=(0, 0),
                    waitBlanking=True,
                    fullscr=self.fullscreen)
                self.ptw.setMouseVisible(False)
                self.ptw.recordFrameIntervals = True

        except Exception as e:
            msg = Exception('[{}] Could not open a "{}" window: {}'.format(__name__, self.display_type, e))
            logging.getLogger('EasyExp').critical(msg)
            raise msg

    def close(self):
        """
        Close window
        :return:
        """
        try:
            if self.display_type == 'qt':
                self.ptw.quit()
            elif self.display_type == 'psychopy':
                self.ptw.setMouseVisible(True)
                logging.getLogger('EasyExp').info('Overall, %i frames were dropped.' % self.ptw.nDroppedFrames)
                import matplotlib.pyplot as plt
                plt.plot(self.ptw.frameIntervals)
                self.ptw.close()
                plt.show()

        except Exception as e:
            msg = Exception('[{}] Could not close a "{}" window: {}'.format(__name__, self.display_type, e))
            logging.getLogger('EasyExp').critical(msg)
            raise msg

    def setptw(self, ptw):
        """
        Set window's pointer
        :param ptw: pointer
        :return:
        """
        self.ptw = ptw

    def getScrRes(self):
        """
        Get full screen resolution
        :return: tuple providing horizontal and vertical screen resolution
        """
        try:
            import Tkinter as Tk
        except ImportError as e:
            msg = ImportError(e)
            logging.getLogger('EasyExp').critical(msg)
            raise msg

        root = Tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.scrRes = (screen_width, screen_height)
        return self.scrRes
