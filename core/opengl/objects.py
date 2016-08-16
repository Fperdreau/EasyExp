#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright © 2013, W. van Ham
'''
from __future__ import print_function
import numpy as np, math, logging
import transforms

""" triangle based objects """


def tetrahedron():
    v = np.array([
        [0.0, math.sqrt(3) / 3, 0.0],
        [-0.5, -math.sqrt(3) / 6, 0.0],
        [0.5, -math.sqrt(3) / 6, 0.0],
        [0.0, 0.0, math.sqrt(6) / 3]
    ], np.float32)
    t = np.array([
        [0, 2, 1],
        [1, 2, 3],
        [2, 3, 0],
        [0, 3, 1]
    ], np.int32)
    return [v, t]


def pyramid():
    v = np.array([
        [-0.5, 0, -0.5],
        [0.5, 0, -0.5],
        [0.5, 0, 0.5],
        [-0.5, 0, 0.5],
        [0, math.sqrt(0.5), 0]
    ], np.float32)
    t = np.array([
        [0, 2, 1],
        [0, 3, 2],
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4],
    ], np.int32)
    return [v, t]


def triangle():
    v = np.array([
        [-0.5, -math.sqrt(3) / 6, 0.0],
        [0.5, -math.sqrt(3) / 6, 0.0],
        [0.0, math.sqrt(3) / 3, 0.0],
    ], np.float32)
    t = np.array([
        [0, 1, 2],
    ], np.int32)
    return [v, t]


def cross():
    """
    Build a fixation cross
    :return:
    """
    v = np.array([
        [-1.0, -0.15, 0.0],  # Horizontal bar start
        [1.0, -0.15, 0.0],
        [-1.0, 0.15, 0.0],  # Horizontal bar end
        [1.0, 0.15, 0.0],
        [-0.15, -1.0, 0.0],  # Vertical bar start
        [0.15, -1.0, 0.0],
        [-0.15, 1.0, 0.0],
        [0.15, 1.0, 0.0]  # Vertical bar end
     ], dtype='float32')

    t = np.array([
        [0, 1, 3],  # Horizontal bar
        [0, 3, 2],
        [4, 5, 7],  # Vertical bar
        [4, 7, 6]
        ], dtype='int32')

    return v, t


def parallelepiped(size):
    """
    Build a parallelepiped
    :param list size: (width, height, depth)
    :return:
    """

    v = np.array([
            [-1.0, -1.0, 1.0],
            [1.0, -1.0, 1.0],
            [-1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [-1.0, -1.0, 0.0],
            [1.0, -1.0, 0.0],
            [-1.0, 1.0, 0.0],
            [1.0, 1.0, 0.0]
        ], dtype='float32')

    # Indexes
    t = np.array([
        [0, 1, 3],  # Front
        [0, 3, 2],
        [1, 5, 7],  # Right
        [1, 7, 3],
        [5, 4, 6],  # Rear
        [5, 6, 7],
        [4, 0, 2],  # Left
        [4, 2, 6],
        [4, 5, 1],  # Bottom
        [4, 1, 0],
        [2, 3, 7],  # Top
        [2, 7, 6]
    ], np.int32)

    return v*np.array(size, dtype='float32'), t


def rim(length=1.0, width=.1, height=.1, nq=10):
    """rim along x axis, length,width, height is x,y,z
    nq is number of quads. Number of quads in arched part is nq-1,
    nq must not be lesss than 2
    todo: normals of v[2] and v[3] are wrong, add a quad
    """

    # declare
    nv = 2 * (nq + 1)
    nv += 2  # add two vertices to give v[2] and v[3] two different normals
    v = np.empty([nv, 3], dtype="float32")
    q = np.empty([nq, 4], dtype="uint32")
    normal = np.empty((nv, 3), dtype="float32")
    xyTex = np.empty((nv, 2), dtype="float32")

    # fill
    v[0] = [-length / 2, 0, 0]
    v[1] = [length / 2, 0, 0]
    v[2] = [-length / 2, 0, height]
    v[3] = [length / 2, 0, height]
    normal[0] = [0, -1, 0]
    normal[1] = [0, -1, 0]
    normal[2] = [0, -.7, .7]  # [0,-1,0] would be correct, but this looks nicer
    normal[3] = [0, -.7, .7]
    xyTex[0] = [0.5 - (length / 2) / (length + 2 * width), 0]
    xyTex[1] = [0.5 + (length / 2) / (length + 2 * width), 0]
    xyTex[2] = [0.5 - (length / 2) / (length + 2 * width), (height) / (width + height)]
    xyTex[3] = [0.5 + (length / 2) / (length + 2 * width), (height) / (width + height)]

    for i in range(2, nv // 2):
        y = width * (i - 2) / (nq - 1)
        x = length / 2 + y
        z = math.sqrt(height ** 2 - (y - width / 2) ** 2)
        v[2 * i] = [-x, y, z]
        v[2 * i + 1] = [x, y, z]
        normal[2 * i] = [0, (y - width / 2) / height, z / height]
        normal[2 * i + 1] = [0, (y - width / 2) / height, z / height]
        xyTex[2 * i] = [0.5 - x / (length + 2 * width), (y + height) / (width + height)]
        xyTex[2 * i + 1] = [0.5 + x / (length + 2 * width), (y + height) / (width + height)]

    q[0] = [0, 1, 3, 2]
    for i in range(2, nq + 1):
        q[i - 1] = [i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2]

    # nicify texture
    xyTex *= .01
    xyTex[:, 0], xyTex[:, 1] = xyTex[:, 1], xyTex[:, 0]

    return (v, q, normal, xyTex)


def edge(size=(1.0, 1.0)):
    """four rims arounds a billiards table"""
    v0, q0, normal0, tex0 = rim(length=size[0], width=.06, height=.04, nq=19)
    # for this texture
    v0[:, 1] += 0.5 * size[1]

    v1, q1, normal1, tex1 = rim(length=size[1], width=.06, height=.04, nq=19)

    R090 = np.array([[0, 1], [-1, 0]])
    R180 = np.array([[-1, 0], [0, -1]])
    R270 = np.array([[0, -1], [1, 0]])
    v1[:, 0:2] = np.dot(v1[:, 0:2], R090)  # rotate left
    v1[:, 0] -= 0.5 * size[0]

    v2, q2, normal2, tex2 = rim(length=size[0], width=.06, height=.04, nq=19)
    v2[:, 0:2] = np.dot(v2[:, 0:2], R180)
    v2[:, 1] -= 0.5 * size[1]

    v3, q3, normal3, tex3 = rim(length=size[1], width=.06, height=.04, nq=19)
    v3[:, 0:2] = np.dot(v3[:, 0:2], R270)
    v3[:, 0] += 0.5 * size[0]


    # combine the four
    v = np.vstack((v0, v1, v2, v3))
    q = np.vstack((q0, q1 + len(v0), q2 + len(v0) + len(v1), q3 + len(v0) + len(v1) + len(v2)))
    normal = np.vstack((normal0, normal1, normal2, normal3))
    tex = np.vstack((tex0, tex1, tex2, tex3))

    return (v, q, normal, tex)


def sphere(r=1.0, nSlices=24, nStacks=18):
    """ radius  Specifies the radius of the sphere.
    slices  Specifies the number of subdivisions around the z axis (similar to lines of longitude).
    stacks  Specifies the number of subdivisions along the z axis (similar to lines of latitude).
    note that there are nStacks-1 duplicate vertices to enable cyclic texture mapping
    """
    if nSlices < 3 or nStacks < 2:
        logging.error("slices<3 or stacks<2")
    nv = 2 + nSlices * (nStacks - 1)
    nt = 2 * nv - 4  # true for all holeless geometries
    nv += nStacks - 1  # duplicate vertices to enable cyclic texture mapping
    v = np.empty([nv, 3], dtype="float32")
    t = np.empty([nt, 3], dtype="uint32")
    xyTex = np.empty((nv, 2), dtype="float32")

    # write vertex positions
    phiValues = np.linspace(0, 2 * math.pi, nSlices + 1, endpoint=True)  # one extra for cyclic texture
    thetaValues = np.linspace(0, math.pi, nStacks, endpoint=False)[1:]
    v[0] = [0, 0, 1]
    xyTex[0] = [0.5, 1]
    iv = 1
    for theta in thetaValues:
        z = math.cos(theta)
        rxy = math.sin(theta)
        for phi in phiValues:
            xyTex[iv] = [phi / (2 * math.pi), 1.0 - theta / math.pi]
            v[iv] = [rxy * math.sin(phi), rxy * math.cos(phi), z]
            iv += 1
    v[-1] = [0, 0, -1]
    xyTex[-1] = [0.5, 0]

    # first row of triangles
    for i in range(nSlices):
        t[i] = [0, 1 + (i + 1) % nSlices, 1 + i % nSlices]
    # triangle strips
    for i in range(nStacks - 2):
        for j in range(nSlices):
            t[nSlices + i * (2 * nSlices) + 2 * j] = [1 + i * (nSlices + 1) + j, 1 + i * (nSlices + 1) + j + 1,
                                                      1 + (i + 1) * (nSlices + 1) + j]
            t[nSlices + i * (2 * nSlices) + 2 * j + 1] = [1 + (i + 1) * (nSlices + 1) + j,
                                                          1 + i * (nSlices + 1) + j + 1,
                                                          1 + (i + 1) * (nSlices + 1) + j + 1]
    # last row of triangles
    for i in range(nSlices):
        t[nt - nSlices + i] = [nv - 1, nv - nSlices - 2 + i, nv - nSlices - 2 + (i + 1)]
    # coordinates, indices, normals, texture coordinates
    return (r * v, t, v, xyTex)


def subdivide(v, t):
    """ subdivide each triangle in three by added a vertex at the CoM,
	    incoming vertex list v is a nv x 3 array of floats,
	    incoming triangle list t is a nt x 3 array of int32,
	"""
    vList = []  # list of new vertices (list of 1D arrays)
    tList = []  # list of all triangles (list of lists of length 3)
    nv = np.shape(v)[0]  # number of vertices to start with
    nt = np.shape(t)[0]  # number of triangles to start with

    for it in range(nt):  # for every triangle
        # lengths of three edges
        edgeLength = [np.linalg.norm(v[t[it][0]] - v[t[it][1]]), np.linalg.norm(v[t[it][1]] - v[t[it][2]]),
                      np.linalg.norm(v[t[it][2]] - v[t[it][0]])]
        sortIndex = np.argsort(edgeLength)
        iv = nv + len(vList)  # index of newly added vertex

        # split low quality triagles in two, if the other triangle is low quality too
        qFactor = 1.4  # 90 deg equilateral triangles have qFactor = sqrt(2)
        if edgeLength[sortIndex[2]] > qFactor * edgeLength[sortIndex[1]]:
            edge = [t[it][sortIndex[2]], t[it][(sortIndex[2] + 1) % 3]]  # indices of the longest edge
            splitEdge = False
            for it2 in range(it + 1, nt):
                if np.any(t[it2] == edge[0]) and np.any(t[it2] == edge[1]):
                    print("found matching triangle")
                    splitEdge = True
                    break
            if splitEdge:
                print("splitting edge ({},{}) of triangles {} and {}".format(edge[0], edge[1], it, it2))
                p = np.mean(v[edge], 0)
                vList.append(p)
                ov = np.logical_and(t[it] != edge[0], t[it] != edge[1]).nonzero()[0][0]  # opposite vertex
                ov2 = np.logical_and(t[it2] != edge[0], t[it2] != edge[1]).nonzero()[0][0]  # opposite vertex
                tList.append([t[it][ov], t[it][(ov + 1) % 3], iv])  # add triangle
                tList.append([t[it][ov], iv, t[it][(ov + 2) % 3]])  # add triangle
                tList.append([t[it2][ov2], t[it2][(ov2 + 1) % 3], iv])  # add triangle
                tList.append([t[it2][ov2], iv, t[it2][(ov2 + 2) % 3]])  # add triangle

                print("  p: {}, ip: {}, ov: {}, ov2: {}".format(p, iv, t[it][ov], t[it2][ov2]))
                print("  new triangles: {} {} {} {}".format(tList[-4], tList[-3], tList[-2], tList[-1]))
            else:
                print("not splitting triangle {}".format(it))
        else:
            # split high quality triagles in three
            print("splitting triangle {} in centroid".format(it, it2, edge))
            p = np.mean(v[t[it]], 0)  # center of mass, coordinate n
            vList.append(p)

            tList.append([t[it][0], t[it][1], iv])  # add triangle
            tList.append([t[it][1], t[it][2], iv])  # add triangle
            tList.append([t[it][2], t[it][0], iv])  # add triangle
            print("  p: {}, ip: {}, new triangles: {} {} {}".format(p, iv, tList[-3], tList[-2], tList[-1]))

    vOut = np.vstack([v, np.array(vList, dtype="float32")])
    tOut = np.array(tList)
    return [vOut, tOut]


def saveOff(v, t, fileName):
    nv = np.shape(v)[0]  # number of vertices to start with
    nt = np.shape(t)[0]  # number of triangles to start with
    with open(fileName, 'w') as f:
        print("OFF", file=f)
        print("{:d} {:d} {:d}".format(nv, nt, 3 * nt / 2), file=f)
        for i in range(nv):
            print("{:6.3f} {:6.3f} {:6.3f}".format(float(v[i][0]), float(v[i][1]), float(v[i][2])), file=f)
        for i in range(nt):
            print("3 {:6d} {:6d} {:6d}".format(t[i][0], t[i][1], t[i][2]), file=f)


if __name__ == "__main__":
    o = sphere(1.0)
    print(o[0])
    print(o[1])
    # o = subdivide(o[0], o[1])
    #print(o[0])
    #print(o[1])
    saveOff(o[0], o[1], "out.off")
	