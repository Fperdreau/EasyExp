#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2015 Wilbert van Ham, Stichting Katholieke Universiteit,
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

import pylink

import pygame
import pygame.mixer
import pygame.event
import pygame.image
import pygame.draw
import pygame.mouse
import array
from pygame.constants import *
from PIL import Image


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


class DisplayPygame(pylink.EyeLinkCustomDisplay):
    """

    """
    def __init__(self, gui):
        pylink.EyeLinkCustomDisplay.__init__(self)

        self.gui = gui
        self.ptw = pygame.display.get_surface()

        if not pygame.mixer.init():
            pygame.mixer.init(44100, -16, 2, 2048)

        self.__target_beep__ = pygame.mixer.Sound("type.wav")
        self.__target_beep__done__ = pygame.mixer.Sound("qbeep.wav")
        self.__target_beep__error__ = pygame.mixer.Sound("error.wav")
        self.imagebuffer = array.array('l')
        self.pal = None
        self.size = (0, 0)

        # Fonts
        if not pygame.font.get_init():
            pygame.font.init()
        self.fnt = pygame.font.Font(None, 20)
        self.fnt.set_bold(1)

        # Mouses
        self.last_mouse_state = -1
        pygame.mouse.set_visible(gui.eyetracker.dummy)

    def setup_cal_display(self):
        """
        Set calibration display
        """
        self.ptw.fill(self.gui.bgcol)
        pygame.display.flip()

    def exit_cal_display(self):
        """
        Exit calibration display
        """
        self.clear_cal_display()

    def record_abort_hide(self):
        pass

    def clear_cal_display(self):
        """
        Clear calibration display
        """
        self.ptw.fill(self.gui.bgcol)
        pygame.display.flip()

    def erase_cal_target(self):
        """
        Erase calibration target
        """
        self.ptw.fill(self.gui.bgcol)

    def draw_cal_target(self, x, y):
        """
        Draw calibration target at the desired location
        :param x:
        :param y:
        """
        outsz = self.gui.targetsize_out  # Target outer size
        insz = self.gui.targetsize_in  # inner dot size
        rect = pygame.Rect(x - outsz[0], y - outsz[1], outsz[0] * 2, outsz[1] * 2)
        pygame.draw.ellipse(self.ptw, self.gui.outer_tgcol, rect)
        rect = pygame.Rect(x - insz[0], y - insz[1], insz[0] * 2, insz[1] * 2)
        pygame.draw.ellipse(self.ptw, self.gui.inner_tgcol, rect)
        pygame.display.flip()

    def play_beep(self, beepid):
        """
        Play a beep as feedback
        :param beepid:
        """
        if beepid == pylink.DC_TARG_BEEP or beepid == pylink.CAL_TARG_BEEP:
            self.__target_beep__.play()
        elif beepid == pylink.CAL_ERR_BEEP or beepid == pylink.DC_ERR_BEEP:
            self.__target_beep__error__.play()
        else:  # CAL_GOOD_BEEP or DC_GOOD_BEEP
            self.__target_beep__done__.play()

    def getColorFromIndex(self, colorindex):
        if colorindex == pylink.CR_HAIR_COLOR:
            return (255, 255, 255, 255)
        elif colorindex == pylink.PUPIL_HAIR_COLOR:
            return (255, 255, 255, 255)
        elif colorindex == pylink.PUPIL_BOX_COLOR:
            return (0, 255, 0, 255)
        elif colorindex == pylink.SEARCH_LIMIT_BOX_COLOR:
            return (255, 0, 0, 255)
        elif colorindex == pylink.MOUSE_CURSOR_COLOR:
            return (255, 0, 0, 255)
        else:
            return (0, 0, 0, 0)

    def draw_line(self, x1, y1, x2, y2, colorindex):
        color = self.getColorFromIndex(colorindex)
        imr = self.__img__.get_rect()

        x1 = int((float(x1) / float(self.size[0])) * imr.w)
        x2 = int((float(x2) / float(self.size[0])) * imr.w)
        y1 = int((float(y1) / float(self.size[1])) * imr.h)
        y2 = int((float(y2) / float(self.size[1])) * imr.h)
        pygame.draw.line(self.__img__, color, (x1, y1), (x2, y2))

    def draw_lozenge(self, x, y, width, height, colorindex):
        color = self.getColorFromIndex(colorindex)

        imr = self.__img__.get_rect()
        x = int((float(x) / float(self.size[0])) * imr.w)
        width = int((float(width) / float(self.size[0])) * imr.w)
        y = int((float(y) / float(self.size[1])) * imr.h)
        height = int((float(height) / float(self.size[1])) * imr.h)

        if width > height:
            rad = height / 2

            #draw the lines
            pygame.draw.line(self.__img__, color, (x + rad, y), (x + width - rad, y))
            pygame.draw.line(self.__img__, color, (x + rad, y + height), (x + width - rad, y + height))

            #draw semicircles
            pos = (x + rad, y + rad)
            clip = (x, y, rad, rad * 2)
            self.__img__.set_clip(clip)
            pygame.draw.circle(self.__img__, color, pos, rad, 1)
            self.__img__.set_clip(imr)

            pos = ((x + width) - rad, y + rad)
            clip = ((x + width) - rad, y, rad, rad * 2)
            self.__img__.set_clip(clip)
            pygame.draw.circle(self.__img__, color, pos, rad, 1)
            self.__img__.set_clip(imr)
        else:
            rad = width / 2

            # draw the lines
            pygame.draw.line(self.__img__, color, (x, y + rad), (x, y + height - rad))
            pygame.draw.line(self.__img__, color, (x + width, y + rad), (x + width, y + height - rad))

            # draw semicircles
            if rad == 0:
                return  # cannot draw sthe circle with 0 radius
            pos = (x + rad, y + rad)
            clip = (x, y, rad * 2, rad)
            self.__img__.set_clip(clip)
            pygame.draw.circle(self.__img__, color, pos, rad, 1)
            self.__img__.set_clip(imr)

            pos = (x + rad, y + height - rad)
            clip = (x, y + height - rad, rad * 2, rad)
            self.__img__.set_clip(clip)
            pygame.draw.circle(self.__img__, color, pos, rad, 1)
            self.__img__.set_clip(imr)

    def get_mouse_state(self):
        """
        Get mouse state: position and input
        :return: object: position and input
        """
        pos = pygame.mouse.get_pos()
        state = pygame.mouse.get_pressed()
        mt = MouseInput(pos, state)

        return mt

    def get_input_key(self):
        """
        Get keyboard input
        :return:
        """
        ky = []
        v = pygame.event.get()
        for key in v:
            if key.type != KEYDOWN:
                continue
            keycode = key.key
            if keycode == K_F1:
                keycode = pylink.F1_KEY
            elif keycode == K_F2:
                keycode = pylink.F2_KEY
            elif keycode == K_F3:
                keycode = pylink.F3_KEY
            elif keycode == K_F4:
                keycode = pylink.F4_KEY
            elif keycode == K_F5:
                keycode = pylink.F5_KEY
            elif keycode == K_F6:
                keycode = pylink.F6_KEY
            elif keycode == K_F7:
                keycode = pylink.F7_KEY
            elif keycode == K_F8:
                keycode = pylink.F8_KEY
            elif keycode == K_F9:
                keycode = pylink.F9_KEY
            elif keycode == K_F10:
                keycode = pylink.F10_KEY

            elif keycode == K_PAGEUP:
                keycode = pylink.PAGE_UP
            elif keycode == K_PAGEDOWN:
                keycode = pylink.PAGE_DOWN
            elif keycode == K_UP:
                keycode = pylink.CURS_UP
            elif keycode == K_DOWN:
                keycode = pylink.CURS_DOWN
            elif keycode == K_LEFT:
                keycode = pylink.CURS_LEFT
            elif keycode == K_RIGHT:
                keycode = pylink.CURS_RIGHT

            elif keycode == K_BACKSPACE:
                keycode = ord('\b')
            elif keycode == K_RETURN:
                keycode = pylink.ENTER_KEY
            elif keycode == K_ESCAPE:
                keycode = pylink.ESC_KEY
            elif keycode == K_TAB:
                keycode = ord('\t')
            elif (keycode == pylink.JUNK_KEY):
                keycode = 0

            ky.append(pylink.KeyInput(keycode, key.mod))
        return ky

    def exit_image_display(self):
        self.clear_cal_display()

    def alert_printf(self, msg):
        print "alert_printf"

    def setup_image_display(self, width, height):
        self.size = (width, height)
        self.clear_cal_display()
        self.last_mouse_state = -1

    def image_title(self, text):
        text = text

        sz = self.fnt.size(text[0])
        txt = self.fnt.render(text, len(text), (0, 0, 0, 255), (255, 255, 255, 255))
        imgsz = (self.size[0] * 3, self.size[1] * 3)
        topleft = ((self.ptw.get_rect().w - imgsz[0]) / 2, (self.ptw.get_rect().h - imgsz[1]) / 2)
        imsz = (topleft[0], topleft[1] + imgsz[1] + 10)
        self.ptw.blit(txt, imsz)
        pygame.display.flip()
        self.ptw.blit(txt, imsz)

    def draw_image_line(self, width, line, totlines, buff):
        # print "draw_image_line", len(buff)
        i = 0
        while i < width:
            self.imagebuffer.append(self.pal[buff[i]])
            i += 1

        if line == totlines:
            imgsz = (self.size[0] * 3, self.size[1] * 3)
            bufferv = self.imagebuffer.tostring()
            img = Image.new("RGBX", self.size)
            img.fromstring(bufferv)
            img = img.resize(imgsz)

            img = pygame.image.fromstring(img.tostring(), imgsz, "RGBX")

            self.__img__ = img
            self.draw_cross_hair()
            self.__img__ = None
            self.ptw.blit(img, ((self.ptw.get_rect().w - imgsz[0]) / 2, (self.ptw.get_rect().h - imgsz[1]) / 2))
            pygame.display.flip()
            self.ptw.blit(img, (
                (self.ptw.get_rect().w - imgsz[0]) / 2, (self.ptw.get_rect().h - imgsz[1]) / 2))  # draw on the back buffer too
            self.imagebuffer = array.array('l')

    def set_image_palette(self, r, g, b):
        self.imagebuffer = array.array('l')
        self.clear_cal_display()
        sz = len(r)
        i = 0
        self.pal = []
        while i < sz:
            rf = int(b[i])
            gf = int(g[i])
            bf = int(r[i])
            self.pal.append((rf << 16) | (gf << 8) | (bf))
            i += 1

    def showmsg(self, msg, color=(255, 255, 255)):
        text = self.fnt.render(msg, 1, color)
        textpos = text.get_rect()
        textpos.centerx = self.ptw.get_rect().centerx
        self.ptw.blit(text, textpos)
        pygame.display.flip()