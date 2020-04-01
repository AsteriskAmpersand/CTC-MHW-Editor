# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 20:29:29 2020

@author: AsteriskAmpersand
"""
from mathutils import Vector, Matrix
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def normalProjection(normal,vector):
    return vector - vector.dot(normal)/normal.length**2*normal

def orientVectorPair(v0,v1):
    v0 = v0.normalized()
    v1 = v1.normalized()
    if v0 == v1:
        return Matrix.Identity(3)
    v = v0.cross(v1)
    #s = v.length
    c = v0.dot(v1)
    if c == -1: return Matrix([[-1,0,0],[0,-1,0],[0,0,1]])
    vx = Matrix([[0,-v[2], v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return Matrix.Identity(3)+vx+(1/(1+c))*vx@vx

zeroVec = [0,0,0]

"""
<Matrix 4x4 ( 0.0000, 1.0000,  0.0000,  0.0000)
            (-0.9063, 0.0000, -0.4226,  0.0000)
            (-0.4226, 0.0000,  0.9063, -0.0000)
            ( 0.0000, 0.0000,  0.0000,  1.0000)>
<Vector (1.0000, 0.0000, 0.0000)>
<Vector (0.0000, -0.9063, -0.4226)>
<Vector (0.1399, -0.9676, -0.2103)>
<Vector (0.9804, 0.1354, 0.0294)>
"""
freeze = Vector((1.0000, 0.0000, 0.0000))
rotate = Vector((0.0000, -0.9063, -0.4226))
target = Vector((0.1399, -0.9676, -0.2103))
projection = normalProjection(freeze,target)
rotator = orientVectorPair(rotate,projection)
goal = rotator@rotate
sidereal = rotator@freeze
soa = np.array([(*zeroVec,*vec) for vec in [freeze,rotate,target,projection,goal,sidereal]])

X, Y, Z, U, V, W = zip(*soa)
fig = plt.figure(figsize = (23,23))
ax = fig.add_subplot(111, projection='3d')
for v,col in zip(soa,["k","b","r","g","c","m"]):
    ax.quiver(*v, color = col)
ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])
plt.show()