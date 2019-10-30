# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 14:09:29 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from mathutils import Vector, Matrix
from ..structures.Ccl import CclFile
import bmesh
from ..operators.ccltools import (findFunction, insertRadiusToMat, transToMat, 
                                    createCapsule, createGeometry, joinEmpties)

class ImportCCL(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ccl"
    bl_label = "Load MHW CCL file (.ccl)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ccl"
    filter_glob = StringProperty(default="*.ccl", options={'HIDDEN'}, maxlen=255)
    
    scale = FloatProperty(
        name = "Multiply sphere radius" ,
        description = "Multiply sphere radii (Factor of 2 according to Statyk)",
        default = 1.0)    

    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        ccl = CclFile(self.properties.filepath)
        for ix, entry in enumerate(ccl.data):
            try:
                capsule = self.recordToCapsule(entry)
                capsule.name = "%d Capsule"%ix
            except Exception as e: 
                print(e)                
        return {'FINISHED'}

    def recordToCapsule(self, record):
        r1,co1 = record.startsphere_radius*self.scale, Vector([record.startsphere_xOffset, 
                                                    record.startsphere_yOffset, 
                                                    record.startsphere_zOffset])
        r2,co2 = record.endsphere_radius*self.scale, Vector([record.endsphere_xOffset,
                                                  record.endsphere_yOffset, 
                                                  record.endsphere_zOffset])
        f1 = findFunction(record.boneIDOne)
        f2 = findFunction(record.boneIDTwo)
        return createCapsule(f1,f2,r1,r2,co1,co2)
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportCCL.bl_idname, text="MHW CCL (.ccl)")
