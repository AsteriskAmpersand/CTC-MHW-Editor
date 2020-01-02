# -*- coding: utf-8 -*-
"""
Created on Sat Nov  9 18:02:02 2019

@author: AsteriskAmpersand
"""


import bpy


class CTCPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__.split('.')[0]

    matrices_buffer = {}
    unknown_bytes_buffer = [0]*5
    chain_buffer = {}
    rotation_buffer : bpy.props.FloatVectorProperty(
        name = 'Rotation Buffer',
        description = 'Stored node rotation matrix',
        precision = 3,
        size = 3,
        subtype = 'EULER'#EULER
    )
    translation_buffer : bpy.props.FloatVectorProperty(
        name = 'Trasnslation Buffer',
        description = 'Stored node translation matrix',
        precision = 3,
        size = 3,
        subtype = 'XYZ'
    )
    unknown_vector_buffer : bpy.props.FloatVectorProperty(
        name = 'Unknown Vector Buffer',
        description = 'Stored unknown vector',
        precision = 3,
        size = 3,
        subtype = 'XYZ'
    )
