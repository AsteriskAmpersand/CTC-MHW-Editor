# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 11:43:04 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from mathutils import Vector, Matrix
from ..structures.Ccl import CCLRecords, CCL
from ..operators.ccltools import getCol

class ExportCCL(Operator, ExportHelper):
    bl_idname = "custom_export.export_mhw_ccl"
    bl_label = "Save MHW CCL file (.ccl)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ccl"
    filter_glob = StringProperty(default="*.ccl", options={'HIDDEN'}, maxlen=255)
    
    scale = FloatProperty(
        name = "Divide sphere radius." ,
        description = "Divide sphere radii when writing back to file (Factor of 2 according to Statyk)",
        default = 1.0)        
    
    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        capsules = self.getCapsules()
        records = [self.capsuleToRecord(capsule) for capsule in capsules]
        binfile = self.recordsToFile(records)
        with open(self.properties.filepath,"wb") as output:
            output.write(binfile.serialize())
        return {'FINISHED'}

    @staticmethod
    def recordsToFile(records):
        return CCL().construct({"Records":records})

    @staticmethod
    def findFunction(functionID):
        match = [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY" 
                 and "boneFunction" in obj and obj["boneFunction"] == functionID]
        if len(match) != 1:
            raise ValueError(("Multiple" if len(match) else "No" )+" Function ID Matches for %d"%functionID)
        return match[0]

    @staticmethod
    def getCapsules():
        return sorted([obj for obj in bpy.context.scene.objects 
                if "Type" in obj and obj["Type"] == "CCL"],key = lambda x: x.name)

    @staticmethod

    def capsuleToRecord(self, capsule):
        data = {}
        offset_matrix1, offset_matrix2 = ExportCCL.getCapsuleMatrices(capsule)
        id1, id2 = ExportCCL.getCapsuleID(capsule)
        trans1 = getCol(offset_matrix1,3)
        scale1 = offset_matrix1[0][0]
        trans2 = getCol(offset_matrix2,3)
        scale2 = offset_matrix2[0][0]
        data["boneIDOne"] = id1
        data["boneIDTwo"] = id2
        data["unknownBytes"] = capsule["Data"]
        data["startsphere"] = trans1
        data["endsphere"] = trans2
        data["startsphere_radius"] = scale1/self.scale
        data["endsphere_radius"] = scale2/self.scale
        return CCLRecords().construct(data)
    
    @staticmethod
    def getCapsuleMatrices(capsule):
        s1,s2 = ExportCCL.getSpheres(capsule)
        return s1.matrix_basis, s2.matrix_basis
    
    @staticmethod
    def getCapsuleID(capsule):
        s1,s2 = ExportCCL.getSpheres(capsule)
        b1 = s1.constraints["Bone Function"].target["boneFunction"]
        b2 = s2.constraints["Bone Function"].target["boneFunction"]
        return b1,b2
    
    @staticmethod
    def getSpheres(capsule):
        s1 = next((empty for empty in capsule.children if empty.type == "EMPTY" 
              and "Type" in empty and empty["Type"] == "CCL_SPHERE" 
              and empty["Position"] == "Start"))
        s2 = next((empty for empty in capsule.children if empty.type == "EMPTY" 
              and "Type" in empty and empty["Type"] == "CCL_SPHERE" 
              and empty["Position"] == "End"))
        return s1, s2
        
    
    
def menu_func_export(self, context):
    self.layout.operator(ExportCCL.bl_idname, text="MHW CCL (.ccl)")
