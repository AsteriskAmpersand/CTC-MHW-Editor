# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 23:04:20 2019

@author: AsteriskAmpersand
"""

"""
import selection_utils

selection_utils.selected #selection in order
"""
import bpy

def createCTCHeader(ucis,uci,ticks,pose,damp,react,grav,windM,windL,windH,ufs):
    header = bpy.data.objects.new("CtcHeader", None )
    bpy.context.scene.objects.link( header )
    #mod.inverse_matrix = node.matrix #experiment into the meaning of the matrix
    header.empty_draw_size = 0
    header.empty_draw_type = "SPHERE"
    header.show_x_ray = True
    for i,ucv in enumerate(ucis): header["unknownsConstantIntSet%d"%i] = ucv 
    header["unknownConstantInt"] = uci
    header["updateTicks"] = ticks
    header["poseSnapping"] = pose
    header["chainDamping"] = damp
    header["reactionSpeed"] = react
    header["gravityMult"] = grav
    header["windMultMid"] = windM
    header["windMultLow"] = windL
    header["windMultHigh"] = windH
    for i,uf in enumerate(ufs): header["unknownFloatSet%d"%i] = uf
    header["Type"] = "CTC"
    return header

def createChain(col,w,ub,xg,yg,zg,xi,yi,zi,uf1,uf2,uf3,wm,lod):
    chain = bpy.data.objects.new("CtcChain", None )
    bpy.context.scene.objects.link( chain )
    chain["Type"] = "CTC_Chain"
    chain.empty_draw_size = .75
    chain.empty_draw_type = "CIRCLE"
    chain.show_x_ray = True
    chain["collision"] = col
    chain["weightiness"] = w
    for i,byte in enumerate(ub): chain["unknownBytes%02d"%i] = byte
    chain["xGravity"] = xg
    chain["yGravity"] = yg
    chain["zGravity"] = zg
    chain["xInertia"] = xi
    chain["yInertia"] = yi
    chain["zInertia"] = zi
    chain["unknownFloatTwo"] = uf1
    chain["unknownFloatThree"] = uf2
    chain["unknownFloatFour"] = uf3
    chain["windMultiplier"] = wm
    chain["lod"] = lod
    return chain