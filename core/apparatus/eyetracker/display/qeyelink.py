#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2015 Wilbert van Ham, Stichting Katholieke Universiteit, 
KVK 41055629, Nijmegen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
This is a Qt widget and program for calibrating an SMI eyelink
This is a very preliminary version.
todo:
- take size of calibration window into account
- use image rather then array of dots for showing the camera image
- go back to tracker.doTrackerSetup() when that is the state of the server
- show controls in program
- get rid of the error of the non-implemented method (error is wrong, but I do not know what method is really meant
- lots more 
"""

import sys, threading, time, collections, random, numpy as np
from PyQt4 import QtCore, QtGui
import pylink


class QEyelink(QtGui.QWidget, pylink.EyeLinkCustomDisplay):
    """
    Use Qt widget as an eyelink (calibration) EyeLinkCustomDisplay
    """

    def __init__(self, tracker):
        """
        Class constructor
        :param tracker:
        :return:
        """
        QtGui.QWidget.__init__(self)
        pylink.EyeLinkCustomDisplay.__init__(self)

        self.tracker = tracker
        print("tracker: {}".format(self.tracker))

        # window initialization
        self.setGeometry(1680, 0, 1680, 1260)
        self.setWindowTitle('Qt Eyelink Calibration')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)  # accept keyboard focus

        self.keyList = collections.deque()

    # self.tracker.doTrackerSetup() # halting

    # QWidget overloaded functions
    def keyPressEvent(self, e):
        print("key pressed: {}".format(e.key()))
        if e.modifiers() and QtCore.Qt.ControlModifier and e.key() == ord("Q"):
            QtCore.QCoreApplication.instance().quit()
        self.keyList.append(e.key())

    def paintEvent(self, event):
        # print("paint")
        # self.qp = QtGui.QPainter()
        # Remember to destroy the QPainter object after drawing. For example:
        qp = QtGui.QPainter()
        qp.begin(self)

        # calibration
        qp.setBrush(QtGui.QColor(255, 0, 0))
        if hasattr(self, 'cal') and self.cal:
            print("drawEllliipse")
            qp.drawEllipse(self.cal[0], self.cal[1], 30, 30)

        # image
        if hasattr(self, 'image') and self.image != None:
            scale = min(self.size().width() // self.imageSize[0], self.size().height() // self.imageSize[1])
            pen = QtGui.QPen()
            pen.setColor(QtGui.QColor(0, 0, 255))
            qp.setPen(pen)
            pen.setWidth(scale)
            for row in range(len(self.image)):
                # print("row: {}".format(float(sum(self.image[row])) / len(self.image[row])))
                for column in range(len(self.image[row])):
                    # print(" ", column, row, self.image[row][column])
                    # self.qp.setPen(QtGui.QColor([16*self.palette[self.image[row][column]]))
                    # self.
                    c = self.palette[self.image[row][column]]
                    pen.setColor(QtGui.QColor(c[0], c[1], c[2]))
                    qp.setPen(pen)
                    # if self.image[row][column] > 10:
                    qp.drawPoint(column * scale, row * scale)
                    # painter.drawImage(source, tempQImage);
        qp.end()

    # EyeLinkCustomDisplay overloaded functions:
    def get_input_key(self):
        """
        Check the event buffer for special key presses
        """

        # the next line is a highly questionable trick to use two event loops in spite of the GIL.
        QtCore.QCoreApplication.instance().processEvents()  # use eyelink event loop for Qt events

        retval = []
        while True:
            try:
                key = self.keyList.popleft()
                if 0x20 <= key < 0x80:
                    k = key  # ascii non-special keys
                elif QtCore.Qt.Key_F1 <= key <= QtCore.Qt.Key_F10:
                    k = pylink.F1_KEY + 0x100 * (key - QtCore.Qt.Key_F1 - 1)  # function keys
                elif key == QtCore.Qt.Key_Enter or key == QtCore.Qt.Key_Return:
                    k = pylink.ENTER_KEY  # main enter or numpad enter
                elif key == QtCore.Qt.Key_Left:
                    k = pylink.CURS_LEFT
                elif key == QtCore.Qt.Key_Up:
                    k = pylink.CURS_UP
                elif key == QtCore.Qt.Key_Right:
                    k = pylink.CURS_RIGHT
                elif key == QtCore.Qt.Key_Down:
                    k = pylink.CURS_DOWN
                elif key == QtCore.Qt.Key_PageUp:
                    k = pylink.PAGE_UP
                elif key == QtCore.Qt.Key_PageDown:
                    k = pylink.PAGE_DOWN
                elif key == QtCore.Qt.Key_Escape:
                    k = pylink.ESC_KEY
                else:
                    k = pylink.JUNK_KEY
                retval.append(pylink.KeyInput(k))
                print("get input: {} -> {}".format(key, k))
            except IndexError:
                return retval

    def play_beep(self, beepid):
        """
        Play a sound during calibration/drift correct.
        :param beepid:
        :return:
        """
        print("beep\a")

    def setup_cal_display(self):
        """
        This function is called just before entering calibration or validation modes
        :return:
        """
        print("setup_cal_display")

    def draw_cal_target(self, x, y):
        """
        Draw calibration/validation target
        :param x:
        :param y:
        :return:
        """
        print("draw cal target {}, {}".format(x, y))
        self.cal = (x, y)
        # always (0, [0, 0, 0, 0], [0, 0, 0, 0])
        # print("crosshair: {}".format(self.tracker.getImageCrossHairData()))
        self.update()

    def exit_cal_display(self):
        """
        This function is called just before exiting calibration/validation mode
        :return:
        """
        print("exit_cal_display")
        self.cal = None
        self.update()

    def record_abort_hide(self):
        """
        This function is called if aborted
        :return:
        """
        print("record abort hide")

    def clear_cal_display(self):
        """
        Clear the calibration display
        :return:
        """
        print("clear cal display")
        self.cal = None
        self.update()

    def erase_cal_target(self):
        """
        Erase the calibration or validation target drawn by previous call to draw_cal_target()
        :return:
        """
        print("erase cal target")
        self.update()

    def setup_image_display(self, width, height):
        print("setup_image_display: {}, {}".format(width, height))
        self.imageSize = (width, height)
        self.image = np.zeros([height, width], dtype="int8")

    def set_image_palette(self, r, g, b):
        """
        Given a set of RGB colors, create a list of 24bit numbers representing the pallet. I.e., RGB of (1,64,127)
        would be saved as 82047, or the number 00000001 01000000 011111111
        :param r: red channel
        :param g: green channel
        :param b: blue channel
        :return:
        """
        print("draw_image_palette: {}".format(zip(r, g, b)))
        self.palette = zip(r, g, b)

    def draw_image_line(self, width, line, totlines, buff):
        """
        Display image given pixel by pixel
        :param width:  pixels in buff
        :param line: index of line (1-totlines)
        :param totlines: total numbers of lines
        :param buff:
        :return:
        """
        # print("draw_image_line: {}, {}, {}, {}".format(width, line, totlines, buff))
        if hasattr(self, 'image'):
            self.image[line - 1][:] = buff
        if line == totlines:
            print("crosshair: {}".format(self.tracker.getImageCrossHairData()))
            self.update()

    def exit_image_display(self):
        print("exit_image_display")
        self.image = None
        self.update()

    def draw_cross_hair(self, surf):
        print("draw_cross_hair: {}".format(surf))

    def alert_printf(self, msg):
        print("alert: {}".format(msg))

    def image_title(self, text):
        # LEFT, HEAD, RIGHT
        print("title: {}".format(text))


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    print("Connecting to eyetracker.")
    tracker = pylink.EyeLink("100.1.1.1")
    # tracker = pylink.EyeLink(None)

    w = QEyelink(tracker)
    app.lastWindowClosed.connect(QtCore.QCoreApplication.instance().quit)
    w.show()
    # tracker.setCalibrationType("HV9")

    # pylink.flushGetkeyQueue()
    pylink.openGraphicsEx(w)
    tracker.doTrackerSetup()
    sys.exit(app.exec_())
