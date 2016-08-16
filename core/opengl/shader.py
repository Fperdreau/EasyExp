#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright © 2013, W. van Ham, Radboud University Nijmegen
This file is part of Sleelab.

Sleelab is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Sleelab is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Sleelab.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys

from OpenGL.GL.shaders import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import *

def initializeShaders(vertexShaderString, fragmentShaderString, geometryShaderString=None):
	if not glUseProgram:
		print ('Missing Shader Objects!')
		sys.exit(1)
	try:
		vertexShader = compileShader(vertexShaderString, GL_VERTEX_SHADER)
		if geometryShaderString !=None:
			geometryShader = compileShader(geometryShaderString, GL_GEOMETRY_SHADER)
		fragmentShader = compileShader(fragmentShaderString, GL_FRAGMENT_SHADER)
	except RuntimeError as (errorString):
		print ("ERROR: Shaders did not compile properly: {}".format(errorString[0]))
		a = (errorString[1][0]).split('\n')
		for i in range(0,len(a)):
			print ("{0:3d} {1:}".format(i+1, a[i]))
		sys.exit(1)
	try:
		if geometryShaderString !=None:
			program = compileProgram(vertexShader, fragmentShader, geometryShader)
		else:
			program = compileProgram(vertexShader, fragmentShader)
	except RuntimeError as (errorString):
		print("ERROR: Shader program did not link/validate properly: {}".format(errorString))
		sys.exit(1)
	
	glUseProgram(program)
	return program

vs = \
"""#version 330
uniform int nFrame;                           // frame number
uniform mat4 MVP;                             // more like VP really

uniform vec3 offset;                          // offset from vertex coordinate (ball position)
uniform float rBalls;

in vec3 position;                             // vertex coordinate
out float normal;                             // vertex normal \dot light dir

void main() {
	vec3 lightDirection = vec3(0.0,1.0,1.0);
	gl_Position = MVP * vec4(position*rBalls+offset, 1.0);
	
	normal = dot(normalize(lightDirection), normalize(position.xyz));
}
"""

fs = \
"""#version 330
uniform vec3 color;
uniform float fadeFactor;   // multiplyer for color (1.0 for faded in, 0.0 for faded out)

in float normal;
out vec4 gl_FragColor;
void main() {
	float ambient = 0.3;
	float diffuse = 1.0;
	if (gl_FrontFacing)
		gl_FragColor = vec4(max(ambient,diffuse*normal)*color, 1.0);
		//gl_FragColor = vec4(max(dot(normal, lightDirection)*diffuse, ambient)*color, 1.0);
		//gl_FragColor = vec4(color*(ambient+dot(normal, lightDirection)), 1.0);
		
	else
		gl_FragColor = vec4(0.0, 0.0, 1.0, 1.0);

}
"""
