#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RuSocSci module for the BITSI extended buttonbox

Copyright (C) 2013,2014 Wilbert van Ham, Radboud University Nijmegen
Distributed under the terms of the GNU General Public License (GPL) version 3 or newer.
"""
import sys, serial, time, os, re, logging, glob
import utils, buttonbox

class Extended(buttonbox.Buttonbox):
	def __init__(self, id=0, port=None):
		[self._device, idString] = utils.open(utils.getPort(id, port))
		if not self._device:
			logging.error("No BITSI extended buttonbox connected.")
		elif idString == "BITSI_extend mode, Ready!":
			logging.debug("Device is a BITSI extended buttonbox ({}): {}".format(len(idString), idString))
		else:
			logging.error("Device is NOT a BITSI extended  buttonbox ({}): {}".format(len(idString), idString))
		self.calibrated = False

	def send(self, val):
		"""
		Set buttonbox LEDs to a certain pattern
		"""
		if self._device == None:
			raise Exception("No buttonbox connected")
		self._device.write(chr(val))
		
	def sendMarker(self, leds=[False,False,False,False,False,False,False,False], val=None):
		if val == None:
			val = 0
			for i in range(8):
				if len(leds)>i:
					if leds[i]:
						val += 1<<i
				else:
					break
		self.send(ord('M'))
		self.send(val)

	def setLeds(self, leds=[False,False,False,False,False,False,False,False], val=None):
		"""
		connect leds to signals output by computer
		"""
		self.send(ord('L'))
		self.send(ord('O'))
		self.sendMarker(leds, val)
		
	def calibrateSound(self):
		self.send(ord('C')) # calibrate sound
		self.send(ord('S'))
		time.sleep(1) # make sure to be silent during the calibration
		self.calibrated = True

	def waitSound(self, flush=True):
		if not self.calibrated:
			logging.debug("calibrating sound, wait 1 s.");
			self.calibrateSound()
		self.send(ord('D')) # detect sound
		self.send(ord('S'))
		if flush:
			self.clearEvents() # flush possible awaiting sound events

