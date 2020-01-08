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
    rotation_buffer = bpy.props.FloatVectorProperty(
        name = 'Rotation Buffer',
        description = 'Stored node rotation matrix',
        precision = 3,
        size = 3,
        subtype = 'EULER'#EULER
    )
    translation_buffer = bpy.props.FloatVectorProperty(
        name = 'Trasnslation Buffer',
        description = 'Stored node translation matrix',
        precision = 3,
        size = 3,
        subtype = 'XYZ'
    )
    unknown_values_buffer = bpy.props.FloatVectorProperty(
        name = 'Unknown Values Buffer',
        description = 'Stored unknown values',
        precision = 3,
        size = 5,
        subtype = 'XYZ'
    )
    unknown_floats_buffer = bpy.props.FloatVectorProperty(
        name = 'Unknown Float Values Buffer',
        description = 'Stored unknown float values',
        precision = 3,
        size = 2,
    )
    unknown_bytes_buffer_l = bpy.props.IntVectorProperty(
        name = 'Unknown Values Buffer',
        description = 'Stored unknown int values',
        size = 3,
        min = 0,
        max = 255,
    )
    unknown_bytes_buffer_r = bpy.props.IntVectorProperty(
        name = 'Unknown Values Buffer',
        description = 'Stored unknown int values',
        size = 2,
        min = 0,
        max = 255,
    )