import sys, time, numpy, struct, os, select, pygame, math, random
from psychopy import event


######################
# JOYSTICK FUNCTIONS #
######################

def flush(f):
	#clears the joystick input file (f, opened previously)
	while len(select.select([f.fileno()], [], [], 0.0)[0])>0:
		os.read(f.fileno(), 4096)


def getPosNonBlocking(f,f_format):
	"""
	wait for a joystick move and set position variables x and y 
	as soon as a new value is available
	"""
	global joy_t, joy_x, joy_y	
	valid = False
	i = 0
	while len(select.select([f.fileno()], [], [], 0.0)[0])>0:
		# while there is something to read from the joystick
		formatSize = struct.calcsize(f_format)
		event = os.read(f.fileno(), formatSize) # non blocking read, maximum size: formatSize
		if len(event) == formatSize:
			(joy_t, value, dunno, axis) = struct.unpack(f_format, event)
			if axis == 0:
				joy_x = value
			elif axis == 1:
				joy_y = value

def GetJoyResponse(time_to_respond):
	if joy_response:
		starttime=time.time()
		running=True
		while running:
			getPosNonBlocking(f2,file_format)
			time.sleep(.1)
			if joy_x > 0.4*xmax:
				response= -1 
				running=False
				resp_time = time.time()- starttime	
			if joy_x < 0.4*xmin:
				response= 1 
				running=False
				resp_time = time.time()	- starttime				
			elif time.time()-starttime>time_to_respond:
				print("WARNING: JOYSTICK TIMEOUT")
				response= 99
				running=False		
				resp_time = time.time()	-starttime
		output = ([response, resp_time])
	return output

#######################
# INITIALIZE JOYSTICK #
#######################

# Select the type of input for the responses 
joy_response= True

if joy_response:
	#I read the values of the axis from the file joy_calibration obtained during calibration
	f=open('/home/experiment/Documents/Antonella/Scripts/joy_calibration.txt' ,"r")
	joy_x = 0
	joy_y = 0 	
	xmax = int(f.readline())
	xmin = int(f.readline())
	ymax = int(f.readline())
	ymin = int(f.readline())
	file_format = 'IhBB' #32 bit unsigned, 16 bit signed, 8 bit unsigned, 8 bit unsigned
	formatSize = struct.calcsize(file_format)
	# open /dev/input/js0 by default or the device given on the command line otherwise
	fileName = "/dev/input/js0"
	# open file in binary mode
	f2 = open(fileName, "rb")
	# discard everything in the joystickbuffer at the moment
	flush(f2)
	print('Joystick initialized\n')
