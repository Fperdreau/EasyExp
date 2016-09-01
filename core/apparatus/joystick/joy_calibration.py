#Joystick calibration routine, calibrates the joystick by moving in all directions 
#and saving the results in a txt file (joy_calibration.txt) as:
# xmax
# xmin 
# ymax 
# ymin
from __future__ import print_function
import struct, time, sys, os, select

#initialize joystick
format = 'IhBB' #32 bit unsigned, 16 bit signed, 8 bit unsigned, 8 bit unsigned
formatSize = struct.calcsize(format)
joy_x = 0
joy_y = 0
joy_t = 0

def getPosNonBlocking(f):
	"""
	wait for a joystick move and set position variables x and y 
	as soon as a new value is available
	"""
	global joy_t, joy_x, joy_y
	
	valid = False
	i = 0
	while len(select.select([f.fileno()], [], [], 0.0)[0])>0:
		# while there is something to read from the joystick
		event = os.read(f.fileno(), formatSize) # non blocking read, maximum size: formatSize
		if len(event) == formatSize:
			(joy_t, value, dunno, axis) = struct.unpack(format, event)
			if axis == 0:
				joy_x = value
			elif axis == 1:
				joy_y = value

def flush(f):
	while len(select.select([f.fileno()], [], [], 0.0)[0])>0:
		os.read(f.fileno(), 4096)

# open /dev/input/js0 by default or the device given on the command line otherwise
fileName = "/dev/input/js0"
# open file in binary mode
f = open(fileName, "rb")
# discard everything in the joystickbuffer at the moment
flush(f)

running = True
xmax = 0
xmin = 0
ymax = 0
ymin = 0
starttime=time.time()

f2=open('/home/experiment/Documents/Antonella/joy_calibration.txt' ,"w")
print("Starting calibration")
while running:			
		getPosNonBlocking(f)
		time.sleep(.1)
		sys.stdout.flush()
		if joy_y > ymax:
			ymax = joy_y
		if joy_y < ymin:
			ymin = joy_y
		if joy_x > xmax:
			xmax = joy_x
		if joy_x < xmin:
			xmin = joy_x
		if time.time()-starttime>30: 
			running = False

print("Obtained values- xmax: {} xmin: {} ymax: {} ymin: {}".format(xmax, xmin, ymax, ymin))

f2.write("{}\n".format(xmax))
f2.write("{}\n".format(xmin))
f2.write("{}\n".format(ymax))
f2.write("{}\n".format(ymin))
f2.close()





