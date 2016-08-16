#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright © 2014, W. van Ham, Radboud University Nijmegen
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

# transforms, create matrices like in the well known GL functions, and more.
# The last 4 elements of the 16 elements matrices are the translation.
# Note that these matrices are for pre-multiplication. (row vector, first transformation 
# first, left to right, Latin order, whatever you name it) Transpose the matrices for 
# post-multiplication.
# Typically one uses y = x M V P, where x is in model coordinates and y is in device coordinates
# - M is the model matrix which transforms from Object Coordinates to World Coordinates, 
# it is different for each object.
# - V is the view matrix which tranforms to Eye Coordinates, where the camera is in the 
#     origin and looks in -z direction. In fixed pipeline applications M * V is called
#     the modelview matrix.
# - P is the projection matrix which transforms to Device Coordinates (or clip coordinates). 
# After this a normalization is performed. (division by w, the fourth coordinate). We now speak
# of Normalized Device Coordinates (NDC). NDC is clipped to -1 -- 1 in each dimension. Last 
# step is transformation to screen coordinates.

import numpy as np, math


def toHom(v):
    """ Cartesian to homogenous """
    return np.hstack((v, np.ones((3.0, 1.0), dtype=v.dtype)))


def fromHom(v):
    return v[:, 0:-1] / v[:, -1][:, None]  # divide by last column


def toTex():
    """from -1 -- 1 homogenious coordinates to 0 -- 1 texture coordinates """
    m = np.matrix([
        [0.5, 0.0, 0.0, 0.0],
        [0.0, 0.5, 0.0, 0.0],
        [0.0, 0.0, 0.5, 0.0],
        [0.5, 0.5, 0.5, 1.0]
    ], np.float32)
    return m


def identity():
    m = np.matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ], np.float32)
    return m


def rotateX(angle):
    return rotate(angle, 1, 0, 0)


def rotateY(angle):
    return rotate(angle, 0, 1, 0)


def rotateZ(angle):
    return rotate(angle, 0, 0, 1)


def rotate(angle, x, y, z):
    c = math.cos(angle * math.pi / 180)
    s = math.sin(angle * math.pi / 180)
    length = np.linalg.norm(np.array([x, y, z]))
    x /= length
    y /= length
    z /= length
    m = np.matrix([
        [x ** 2 * (1 - c) + c, x * y * (1 - c) + z * s, x * z * (1 - c) - y * s, 0],
        [y * x * (1 - c) - z * s, y ** 2 * (1 - c) + c, y * z * (1 - c) + x * s, 0],
        [x * z * (1 - c) + y * s, y * z * (1 - c) - x * s, z ** 2 * (1 - c) + c, 0],
        [0, 0, 0, 1]
    ], np.float32)
    return m


def translate(x, y=0, z=0):
    m = np.matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [x, y, z, 1.0]
    ], np.float32)
    return m


def translateV(p):
    return translateMatrix(p[0], p[1], p[2])


def lookAtV(eye, center, up):
    # build view matrix, center is center of view
    # for an eye in the origin, looking in the negative z direction, with y=up, this is identity
    f = center - eye
    f /= np.linalg.norm(f)
    up /= np.linalg.norm(up)
    s = np.cross(f, up)
    u = np.cross(s, f)
    m = np.matrix([
        [s[0], u[0], -f[0], 0.0],
        [s[1], u[1], -f[1], 0.0],
        [s[2], u[2], -f[2], 0.0],
        [-eye[0], -eye[1], -eye[2], 1.0]
    ], np.float32)
    return m


def lookAt(eyeX, eyeY, eyeZ, centerX, centerY, centerZ, upX, upY, upZ):
    return lookAtV(
        np.array([eyeX, eyeY, eyeZ]),
        np.array([centerX, centerY, centerZ]),
        np.array([upX, upY, upZ])
    )


def ortho(left, right, bottom, top, near, far):
    # build projection matrix
    tx = -(right + left)
    ty = -(top + bottom)
    tz = -(far + near)
    m = np.matrix([
        [2. / (right - left), 0, 0, 0],
        [0, 2. / (top - bottom), 0, 0],
        [0, 0, -2. / (far - near), 0],
        [tx, ty, tz, 1]
    ], np.float32)
    return m


def perspective(fovy_deg, aspect, near, far):
    # build projection matrix (like gluPerspective)
    # aspect is width/height. note that near and far are distances, not coordinates
    fov = math.radians(fovy_deg)
    f = 1.0 / math.tan(fov / 2.0)
    m = np.matrix([
        [f / aspect, 0.0, 0.0, 0.0],
        [0.0, f, 0.0, 0.0],
        [0.0, 0.0, (far + near) / (near - far), -1.0],
        [0.0, 0.0, 2.0 * far * near / (near - far), 0.0]
    ], np.float32)
    return m


def frustum(left, right, bottom, top, near, far):
    # build projection matrix
    # note that near and far are distances, not coordinates
    # top, bottom, left and right are at the near plane
    m = np.matrix([
        [2 * near / (right - left), 0.0, 0.0, 0.0],
        [0.0, 2 * near / (top - bottom), 0.0, 0.0],
        [0.0, 0.0, (far + near) / (near - far), -1.0],
        [0.0, 0.0, 2.0 * far * near / (near - far), 0.0]
    ], np.float32)
    return m


def arjan(width, height, near, focal, far, x, y):
    """
    build MVP matrix, width and height are at the focal plane (which is at z=0).
    near, focal and far are distances to these planes.
    x, y is the viewer position in the z=focal plane
    """
    m = np.matrix([
        2 * focal / width, 0, 0, 0,
        0, 2 * focal / height, 0, 0,
        -2 * x / width, -2 * y / height, (far + near) / (near - far), -1,
        0, 0, (2 * far * near - focal * (far + near)) / (near - far), focal
    ], np.float32)
    return m

