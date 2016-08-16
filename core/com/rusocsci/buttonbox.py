#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RuSocSci module for the BITSI buttonbox

Copyright (C) 2013-2014 Wilbert van Ham, Radboud University Nijmegen
Distributed under the terms of the GNU General Public License (GPL) version 3 or newer.
"""
import sys, serial, time, os, re, logging, glob
import utils

# our buttonbox has id 0403:6001 fro  its UART IC
# todo: add support for 2341:0001 (Arduino Uno)
# make sure you have the pyusb module installed
# for window you may need this: http://sourceforge.net/apps/trac/libusb-win32/wiki

class Buttonbox(object):
	"""
	Object that connects tot RuSocSci BITSI buttonbox. Typical usage::

		from rusocsci import buttonbox

		bb = buttonbox.Buttonbox() # connect to last inserted buttonbox

		print("Press any key")
		l = bb.waitKeys(10)
		if l:
			print("key pressed: {}".format(l[0]))
		else:
			print("no key pressed.")

	or for non-blocking input (using the Python 3 print function)::

		from __future__ import print_function
		from rusocsci import buttonbox
		import time, sys

		bb = buttonbox.Buttonbox() # connect to last inserted buttonbox

		print("Press any key")
		while not len(bb.getKeys()): # while there is no input
			print(".", end='')
			sys.stdout.flush()
			time.sleep(1)

	"""
	def __init__(self, id=0, port=None):
		self._port = utils.getPort(id, port)
		self._device = None
		if not self._port:
			raise Exception("No USB serial device connected, could not get port name.")
		[self._device, idString] = utils.open(self._port)
		if not self._device:
			logging.critical("No BITSI buttonbox connected, could not connect to port {}".format(self._port))
		elif idString == "BITSI mode, Ready!" or idString == "BITSI event mode, Ready!":
			logging.debug("Device is a BITSI buttonbox ({}): {}".format(len(idString), idString))
		else:
			logging.error("Device is NOT a BITSI buttonbox ({}): {}".format(len(idString), idString))

	def close(self):
		if self._device:
			self._device.close()
				
	def clearEvents(self):
		"""
		Clear previous events that are still in the input buffer.
		"""
		if self._device == None:
			raise Exception("No buttonbox connected")
		try:
			self._device.flushInput()
		except Exception as e:
			raise Exception("Could not clear buttonbox buffer:\n{}".format(e))
		
	def getButtons(self, buttonList=None):
		"""
		Returns a list of buttons that were pressed on the buttonbox. 

		:Parameters:
			buttonList : **None** or []
				Allows the user to specify a set of keys to check for.
				Only keypresses from this set of keys will be removed from the keyboard buffer.
				If the keyList is None all keys will be checked and the key buffer will be cleared
				completely. NB, pygame doesn't return timestamps (they are always 0)
			timeStamped : **False** or True or `Clock`
				If True will return a list of
				tuples instead of a list of keynames. Each tuple has (keyname, time).
				If a `core.Clock` is given then the time will be relative to the `Clock`'s last reset
				there is no timestamp in our buttonbox. Use buttonbox.waitkeys if you want timestamps.
		"""
		if self._device == None:
			raise Exception("No buttonbox connected")
		
		self._device.timeout = 0
		cList = self._device.read(1024)
		#if len(cList)>0:
			#logging.debug("read {} bytes: {}".format(len(cList), cList))
		cListSelected = []
		for c in cList:
			if buttonList==None or c in buttonList:
				cListSelected.append(c)
		return cListSelected

	def getKeys(self, keyList=None):
		"""
		Mutatis Mutandis identical to getButtons
		"""
		return self.getButtons(buttonList=keyList)

				
	def waitButtons(self, maxWait=float("inf"), buttonList=None, timeStamped=False, flush=True):
		"""
		Same as getButtons(), but halts everything (including drawing) while awaiting
		input from buttonbox. Implicitly clears buttonbox, so any preceding buttonpresses will be lost.

		:Parameters:
			maxWait : any numeric value.
				Maximum number of seconds period and which buttons to wait for. 
				Default is float('inf') which simply waits forever.
			buttonList:
				List of one character strings containing the buttons to react to.
				All other button presses will be ignored. Note that for BITSI 
				buttonboxes the buttons are identified by capital letters upon press
				and by lower case letters upon release.

		Returns None if times out. Returns a list of one character upon succes, like 
		the PsychoPy event module.
		"""
		if self._device == None:
			raise Exception("No buttonbox connected")
				
		if flush:
			self._device.flushInput()
		t = time.time()
		while maxWait > time.time() - t:
			if maxWait == float("inf"):
				self._device.timeout = None
			else:
				self._device.timeout = maxWait - (time.time() - t)
			c = self._device.read(1)
			if buttonList==None or c in buttonList:
				# return
				break
			else:
				# as if nothing pressed
				c = ''
		if c=='':
			# version 0.7 addition to comply with PsychoPy
			return None
		if hasattr(timeStamped, 'timeAtLastReset'):
			return [(c, time.time() - timeStamped.timeAtLastReset)]
		elif timeStamped:
			# return as a one item list to mimic getButtons behaviour
			return [(c, time.time() - t)]
		else:
			return [c] # version 0.7 change to comply with PsychoPy
			
	def waitKeys(self, maxWait=float("inf"), keyList=None, timeStamped=False):
		"""
		Mutatis Mutandis identical tot waitButtons
		"""
		return self.waitButtons(maxWait=maxWait, buttonList=keyList, timeStamped=False, flush=True)

	def setLeds(self, leds=[False,False,False,False,False,False,False,False], val=None):
		"""
		Set buttonbox LEDs to a certain pattern
		"""
		if self._device == None:
			raise Exception("No buttonbox connected")
		if val == None:
			val = 0
			for i in range(8):
				if len(leds)>i:
					if leds[i]:
						val += 1<<i
				else:
					break
		self._device.write(chr(val))
		
	def sendMarker(self, markers=[False,False,False,False,False,False,False,False], val=None):
		"""
		Mutatis Mutandis identical to setLeds()
		"""
		return self.setLeds(leds=markers, val=val)

	def waitLeds(self, leds=[False,False,False,False,False,False,False,False], wait=1.0, val=None):
		"""
		Set buttonbox LEDs to a certain pattern and wait a while. Reset afterwards.
		"""
		if self._device == None:
			raise Exception("No buttonbox connected")
		self.setLeds(leds, val)
		time.sleep(wait)
		self.setLeds()
		