# -*- coding: utf-8 -*-
#
# display_psychopy.py
#
# Copyright (C) 2011 Jason Locklin
# Distributed under the terms of the GNU General Public License (GPL).
#
# Provides a standard set of functions for using an eye tracker that
# allows experiment code to be simple and tracker agnostic.
#
# This module provides a generic interface for eye trackers
# use the following to load:
# from eyeTracker import Tracker_Eyelink as Tracker
# or
# from eyeTracker import Tracker_dummy as Tracker
# etc.
# That way, an experiment can be switched from one eyetracker
# to another without changing any code beyond this one line.
# Note: import eyeTracker before numpy or psychopy

import pylink
import pygame
import pygame.event
from pygame.constants import *

import sys
import os
from psychopy import visual, event, sound, __version__ as psychopy_ver
import numpy as np
import array

from PIL import Image

import inspect
from os.path import dirname
import logging

RIGHT_EYE = 1
LEFT_EYE = 0
BINOCULAR = 2
HIGH = 1
LOW = 0
WHITE = (255, 255, 255)
GRAY = GREY = (128, 128, 128)
BLACK = (0, 0, 0)
buttons = (0, 0)
spath = os.path.dirname(sys.argv[0])
if len(spath) != 0:
    os.chdir(spath)


class KeyInput:
    def __init__(self, key, state=0):
        self.__key__ = key
        self.__state__ = state
        self.__type__ = 0x1


class MouseInput:
    def __init__(self, pos, state=0):
        self.__position__ = pos
        self.__state__ = state
        self.__type__ = 0x1


class EyeLinkCoreGraphicsPsychopy(pylink.EyeLinkCustomDisplay):
    """
    EyeLinkCoreGraphicsPsychopy class
    Implement display of eye-tracker calibration
    """

    def __init__(self, tracker, ptw, dummy=False, bgcol=(0, 0, 0), outer_target_size=30, inner_target_size=30,
                 outer_target_col=(.5, .5, .5), inner_target_col=(0, 0, 0)):
        """
        Initialize a Custom EyeLinkCoreGraphics for Psychopy
        :param tracker: the TRACKER() object
        :param ptw: the Psychopy display window
        :param bgcol: background color
        """
        pylink.EyeLinkCustomDisplay.__init__(self)
        self.tracker = tracker
        self.ptw = ptw

        __FOLDER__ = dirname(dirname(inspect.getfile(self.__class__)))

        # Mouse
        # =====
        self.ptw.mouseVisible = dummy
        self.mouse = event.Mouse(visible=dummy, win=ptw)
        self.mouse.setPos([0, 0])  # make the mouse appear at the center of the camera image
        self.last_mouse_state = -1

        # Display settings
        self.units = 'pix'
        self.displaySize = ptw.size
        self.bgcol = bgcol  # Background color
        self.xc = self.displaySize[0]*0.5
        self.yc = self.displaySize[1]*0.5
        self.sizeX = ptw.size[0]
        self.sizeY = ptw.size[1]
        self.ld = 40  # Line height in pixels
        self.fontsize = 15
        self.extra_info = True
        self.display_open = True
        self.state = None

        # Target properties
        # =================
        self.targetsize_out = outer_target_size
        self.outer_tgcol = outer_target_col
        self.targetsize_in = inner_target_size
        self.inner_tgcol = inner_target_col

        # Eye Image properties
        # ================
        self.imgBuffInitType = 'l'
        self.imagebuffer = array.array(self.imgBuffInitType)
        # scaling of the camera image, must be an integer, i.e., 1,2,3
        self.sf = 2

        self.tmp_file = "{}/dump_img.jpg".format(__FOLDER__)

        self.pal = None
        self.size = (384, 320)

        # image title
        self.title = visual.TextStim(self.ptw, '', height=self.size[1]*self.sf/20)

        # lines
        self.line = visual.Line(self.ptw, start=(0, 0), end=(0, 0), lineWidth=1.0, lineColor=[0, 0, 0])

        # check psychopy version
        self.psychopyVer = psychopy_ver

        # set some useful parameters
        self.keys = []
        ws = np.array(self.displaySize)
        self.img_span = 1.5 * np.array((float(ws[0]) / ws[1], 1.))

        # Colors
        self.color = {
                pylink.CR_HAIR_COLOR: pygame.Color('white'),
                pylink.PUPIL_HAIR_COLOR: pygame.Color('white'),
                pylink.PUPIL_BOX_COLOR: pygame.Color('green'),
                pylink.SEARCH_LIMIT_BOX_COLOR: pygame.Color('red'),
                pylink.MOUSE_CURSOR_COLOR: pygame.Color('red'),
                'font': pygame.Color('white'),
                }

        # Sounds
        self.__target_beep__ = sound.Sound('{}/sounds/type.wav'.format(__FOLDER__))
        self.__target_beep__done__ = sound.Sound('{}/sounds/qbeep.wav'.format(__FOLDER__))
        self.__target_beep__error__ = sound.Sound('{}/sounds/error.wav'.format(__FOLDER__))

    def setup_event_handlers(self):
        """
        Set label
        """
        self.label = visual.TextStim(self.ptw, text='Eye Label', units='norm',  pos=(0, -self.img_span[1] / 2.),
                                     color='white')

    def draw_menu_screen(self):
        """
        Draws the menu screen.
        """
        msgs = ("Eyelink calibration menu", "Press C to calibrate", "Press V to validate", "Press A to auto-threshold",
                "Press I to toggle extra info in camera image", "Press Enter to show camera image", "Press ESC to abort calibration", "Press Q to exit menu");
        pos = .9
        for msg in msgs:
            print(msg)
            text = visual.TextStim(self.ptw, text=msg, pos=(0, pos), units='norm', color=(1, 1, 1))
            text.draw()
            pos -= .1

    def setup_cal_display(self):
        """
        This function is called just before entering calibration or validation modes
        """
        self.ptw.setColor(self.bgcol)
        self.draw_menu_screen()
        self.ptw.flip()

    def exit_cal_display(self):
        """
        This function is called just before exiting calibration/validation mode
        """
        self.ptw.setColor(self.bgcol)
        self.clear_cal_display()

    def record_abort_hide(self):
        """
        This function is called if aborted
        """
        pass

    def clear_cal_display(self):
        """
        Clear the calibration display
        Returns
        -------
        void
        """
        self.ptw.setColor(self.bgcol)
        self.ptw.flip(clearBuffer=True)

    def erase_cal_target(self):
        """
        Erase the calibration or validation target drawn by previous call to draw_cal_target()
        Returns
        -------
        void
        """
        self.ptw.setColor(self.bgcol)
        self.ptw.flip(clearBuffer=True)

    def play_beep(self, beepid):
        """
        Play a sound during calibration/drift correct.
        :param beepid:
        :return:
        """
        if beepid == pylink.CAL_TARG_BEEP or beepid == pylink.DC_TARG_BEEP:
            self.__target_beep__.play()
        if beepid == pylink.CAL_ERR_BEEP or beepid == pylink.DC_ERR_BEEP:
            self.__target_beep__error__.play()
        if beepid in [pylink.CAL_GOOD_BEEP, pylink.DC_GOOD_BEEP]:
            self.__target_beep__done__.play()

    def draw_cal_target(self, x, y):
        """
        Draw calibration/validation target
        Parameters
        ----------
        :param x: horizontal coordinate
        :param y: vertical coordinate

        Returns
        -------
        void
        """
        pos = x - self.displaySize[0]/2, -(y-self.displaySize[1]/2)
        outer_target = visual.PatchStim(self.ptw, tex=None, mask='circle',
                                        units=self.units, pos=pos,
                                        size=self.targetsize_out,
                                        color=self.outer_tgcol)
        inner_target = visual.PatchStim(self.ptw, tex=None, mask='circle',
                                        units=self.units, pos=pos,
                                        size=self.targetsize_in,
                                        color=self.inner_tgcol)
        outer_target.draw()
        inner_target.draw()
        self.ptw.flip()

    def draw_fixation(self, x, y, flip=True):
        """
        Draw fixation point
        Parameters
        ----------
        :param x: horizontal coordinate
        :param y: vertical coordinate
        :param flip: do we flip the screen

        Returns
        -------
        void
        """
        outer_target = visual.PatchStim(self.ptw, tex=None, mask='circle',
                                        units=self.units, pos=(x, y),
                                        size=self.targetsize_out,
                                        color=self.outer_tgcol)
        inner_target = visual.PatchStim(self.ptw, tex=None, mask='circle',
                                        units=self.units, pos=(x, y),
                                        size=self.targetsize_in,
                                        color=self.inner_tgcol)
        outer_target.draw()
        inner_target.draw()

        if flip:
            self.ptw.flip()

    def draw_eye(self, x, y, flip=True):
        """
        Renders a circle to simulate gaze position on the screen
        Parameters
        ----------
        :param x: horizontal coordinate
        :param y: vertical coordinate
        flip: do we flip the screen
        :type flip bool

        Returns
        -------
        void
        """
        eye = visual.PatchStim(self.ptw, tex=None, mask='circle',
                               units=self.units, pos=(x, y),
                               size=(20, 20), color='red')
        eye.draw()
        if flip:
            self.ptw.flip()

    def play_beep(self, beepid):
        """ Play a sound during calibration/drift correct."""
        pass

    def getColorFromIndex(self, colorindex):
        """Return psychopy colors for varius objects"""
        if colorindex == pylink.CR_HAIR_COLOR:
            return 255, 255, 255, 255
        elif colorindex == pylink.PUPIL_HAIR_COLOR:
            return 255, 255, 255, 255
        elif colorindex == pylink.PUPIL_BOX_COLOR:
            return 0, 255, 0, 255
        elif colorindex == pylink.SEARCH_LIMIT_BOX_COLOR:
            return 255, 0, 0, 255
        elif colorindex == pylink.MOUSE_CURSOR_COLOR:
            return 255, 0, 0, 255
        else:
            return 0, 0, 0, 0

    def draw_losenge(self, x, y, width, height, colorindex):
        """Draw the cross hair at (x,y) """
        color = self.getColorFromIndex(colorindex)

    def get_mouse_state(self):
        """Get the current mouse position and status"""
        pygame.event.pump()
        pos = self.mouse.getPos()
        state = self.mouse.getPressed()[0]
        mt = MouseInput(pos, state)
        return mt

    def key_mapping(self, event):
        """
        Maps key input to Eyelink standards
        :rtype : object
        """
        if event.type == KEYDOWN:
            if event.key == pygame.K_F1:
                key = pylink.F1_KEY
            elif event.key == pygame.K_F2:
                key = pylink.F2_KEY
            elif event.key == pygame.K_F3:
                key = pylink.F3_KEY
            elif event.key == pygame.K_F4:
                key = pylink.F4_KEY
            elif event.key == pygame.K_F5:
                key = pylink.F5_KEY
            elif event.key == pygame.K_F6:
                key = pylink.F6_KEY
            elif event.key == pygame.K_F7:
                key = pylink.F7_KEY
            elif event.key == pygame.K_8:
                key = pylink.F8_KEY
            elif event.key == pygame.K_F9:
                key = pylink.F9_KEY
            elif event.key == pygame.K_F10:
                key = pylink.F10_KEY
            elif event.key == pygame.K_PAGEUP:
                key = pylink.PAGE_UP
            elif event.key == pygame.K_PAGEDOWN:
                key = pylink.PAGE_DOWN
            elif event.key == pygame.K_UP:
                key = pylink.CURS_UP
            elif event.key == pygame.K_DOWN:
                key = pylink.CURS_DOWN
            elif event.key == pygame.K_LEFT:
                key = pylink.CURS_LEFT
            elif event.key == pygame.K_RIGHT:
                key = pylink.CURS_RIGHT
            elif event.key == pygame.K_BACKSPACE:
                key = '\b'
            elif event.key == pygame.K_RETURN:
                key = pylink.ENTER_KEY
            elif event.key == pygame.K_ESCAPE:
                key = pylink.ESC_KEY
            elif event.key == K_TAB:
                key = '\t'
            elif event.key == pygame.K_c:
                key = pygame.K_c
            elif event.key == pygame.K_v:
                key = pygame.K_v
            else:
                key = event.key

            if key == pylink.JUNK_KEY:
                return 0
            print('Pressed key is: {}'.format(key))
            return key

        return 0

    def get_input_key(self):
        ky = []
        pygame.event.pump()
        for key in pygame.event.get([KEYDOWN]):
            tkey = self.key_mapping(key)
            # getKeys does not retrun key modifiers, this workaround doe not work
            if tkey in ['lshift', 'rshift']:
                mod = 1
            else:
                mod = 0
            ky.append(pylink.KeyInput(tkey, mod))
        pygame.event.clear()
        return ky

    def exit_image_display(self):
        '''Called to end camera display'''
        self.ptw.flip()

    def alert_printf(self, msg):
        '''Print error messages.'''
        print("Eyelink alert: {}".format(msg))

    def _img2win(self, x, y):
        """Convert window coordinates to img coordinates"""
        bounds, scale = self.img.bounds, self.img.scale
        x = int(scale * x + bounds[0])
        y = int(bounds[3] - scale * y)
        return x, y

    def setup_image_display(self, w, h):
        """
        convert w, h from pixels to relative units
        :param w:
        :param h:
        :return:
        """
        self.size = (w, h)
        # self.clear_cal_display()
        self.title.autoDraw = True
        self.last_mouse_state = -1

    def image_title(self, text):#
        '''Draw title text at the bottom of the screen for camera setup'''
        # self.clear_cal_display()
        title_pos = (0, 0-self.size[0]*self.sf/2.0-20)
        self.title.pos = title_pos
        self.title.text = text

    def set_image_palette(self, r,g,b): #
        '''Given a set of RGB colors, create a list of 24bit numbers representing the pallet.
        I.e., RGB of (1,64,127) would be saved as 82047, or the number 00000001 01000000 011111111'''
        self.imagebuffer = array.array(self.imgBuffInitType)
        # self.clear_cal_display()
        sz = len(r)
        i =0
        self.pal = []
        while i < sz:
            rf = int(b[i])
            gf = int(g[i])
            bf = int(r[i])
            self.pal.append((rf << 16) | (gf << 8) | bf)
            i += 1

    def draw_title(self):
        """
        desc:
            Draws title info.
        """
        y = 0
        for line in self.title:
            surf = self.font.render(line, 0, self.color['font'])
            self.cam_img.blit(surf, (1, y))
            y += 12

    def draw_cross_hair(self):
        """
        Draw a cross hair
        :return:
        """
        pass

    def draw_image_line_new(self, width, line, totlines, buff):  #
        '''Display image given pixel by pixel'''
        i = 0
        while i < width:
            self.imagebuffer.append(self.pal[buff[i]])
            i += 1

        if line == totlines:
            bufferv = self.imagebuffer.tostring()
            if float(self.psychopyVer[:4]) < 1.83:
                img = Image.fromstring("RGBX", (width, totlines), bufferv)
            else:
                img = Image.frombytes("RGBX", (width, totlines), bufferv)

            imgResize = img.resize((self.size[0] * self.sf, self.size[1] * self.sf))
            imgResizeVisual = visual.ImageStim(self.ptw, image=imgResize)

            imgResizeVisual.draw()
            self.draw_cross_hair()
            self.ptw.flip()

            self.imagebuffer = array.array(self.imgBuffInitType)

    def draw_image_line(self, width, line, totlines, buff):
        """
        Draws a single eye video frame, line by line.
        Arguments:
        width		--	Width of the video.
        line		--	Line nr of current line.
        totlines	--	Total lines in video.
        buff		--	Frame buffer.
        imagesize	--	The size of the image, which is (usually?) 192x160 px.
        """

        # If the buffer hasn't been filled yet, add a line.
        for i in range(width):
            try:
                self.imagebuffer.append(self.pal[buff[i]])
            except:
                pass

        # If the buffer is full, push it to the display.
        if line == totlines:
            self.sf = totlines/320.
            self._size = int(self.sf*self.size[0]), int(
                self.sf*self.size[1])
            # Convert the image buffer to a pygame image, save it ...
            try:
                # This is based on PyLink >= 1.1
                self.cam_img = pygame.image.fromstring(
                    self.imagebuffer.tostring(), self._size, 'RGBX')
            except:
                # This is for PyLink <= 1.0. This try ... except construction
                # is a hack. It would be better to understand the difference
                # between these two versions.
                self.cam_img = pygame.image.fromstring(
                    self.imagebuffer.tostring(), self.size, 'RGBX')
                self.sf = 1.
            if self.extra_info:
                self.draw_cross_hair()
                #self.draw_title()

            pygame.image.save(self.cam_img, self.tmp_file)

            # ... and then show the image.
            self.ptw.flip()
            imgStim = visual.ImageStim(self.ptw, image=self.tmp_file, size=self.sf*self.size[0])
            imgStim.draw()
            self.ptw.flip()

            # Clear the buffer for the next round!
            self.imagebuffer = array.array('L')

    def draw_line(self, x1, y1, x2, y2, colorindex):
        """
        Unlike the function name suggests, this draws a single pixel. I.e.
        the end coordinates are always exactly one pixel away from the start
        coordinates.
        Arguments:
        x1			--	The starting x.
        y1			--	The starting y.
        x2			--	The end x.
        y2			--	The end y.
        colorIndex	--	A color index.
        """
        y1 = y1 * -1 + self.size[1] / 2
        x1 = x1 * 1 - self.size[0] / 2
        y2 = y2 * -1 + self.size[1] / 2
        x2 = x2 * 1 - self.size[0] / 2

        color = self.getColorFromIndex(colorindex)
        self.line.start = (x1 * self.sf, y1 * self.sf)
        self.line.end = (x2 * self.sf, y2 * self.sf)
        self.line.lineColor = color
        self.line.draw()

    def draw_lozenge(self, x, y, w, h, colorindex):
        """
        desc:
            Draws a rectangle.
        arguments:
            x:
                desc:	X coordinate.
                type:	int
            y:
                desc:	Y coordinate.
                type:	int
            w:
                desc:	A width.
                type:	int
            h:
                desc:	A height.
                type:	int
            colorindex:
                desc:	A colorindex.
                type:	int
        """
        x = int(self.scale*x)
        y = int(self.scale*y)
        w = int(self.scale*w)
        h = int(self.scale*h)
        self.loz_circ = visual.Circle(self.ptw, color=self.getColorFromIndex(colorindex), pos=(x, y), units='pix',
                                      radius=(w, h), lineWidth=2)
        self.loz_circ.draw()

    def showmsg(self, msg, color=(255, 255, 255)):
        """
        Display a message (used by fixation test)
        :param msg: string
        :param color: text color
        :return:
        """
        text = visual.TextStim(self.ptw, text=msg, color=color, alignHoriz='center',
                               alignVert=self.yc - 50)
        text.draw()
        self.ptw.flip()
