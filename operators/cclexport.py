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
    
    missingFunctionBehaviour = EnumProperty(
            name = "Missing Bone Functions",
            description = "Determines what to do while opening a file with missing bone functions",
            items = [("Abort","Abort","Aborts exporting process",0),
                     ("Omit","Omit","Omit the sphere pair",1),
                     ("Dummy","Dummy","Sets the bone function to 255 and continues creating the capsule",2)],
            default = "Truncate"
            )    
    
    def execute(self,context):
        self.errors = []
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        capsules = self.getCapsules()
        records = []
        for capsule in capsules:
            try: records.append(self.capsuleToRecord(capsule))
            except: 
                if self.missingFunctionBehaviour == "Abort": 
                    self.displayErrors(self.errors)
                    return {'CANCELED'}
        binfile = self.recordsToFile(records)
        with open(self.properties.filepath,"wb") as output:
            output.write(binfile.serialize())
        return {'FINISHED'}

    @staticmethod
    def recordsToFile(records):
        return CCL().construct({"Records":records})

    @staticmethod
    def getCapsules():
        return sorted([obj for obj in bpy.context.scene.objects 
                if "Type" in obj and obj["Type"] == "CCL"],key = lambda x: x.name)

    def capsuleToRecord(self, capsule):
        data = {}
        offset_matrix1, offset_matrix2 = ExportCCL.getCapsuleMatrices(capsule)
        try: id1, id2 = self.getCapsuleID(capsule)
        except: raise ValueError
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
    

    def getFunction(self, sphere):
        try: return sphere.constraints["Bone Function"].target["boneFunction"]
        except:
            self.errors.append("Missing Bone Function on Node %s"%sphere.name)
            if self.missingFunctionBehaviour == "Dummy": return 255
            else: raise ValueError

    def getCapsuleID(self, capsule):
        s1,s2 = ExportCCL.getSpheres(capsule)
        b1 = self.getFunction(s1)
        b2 = self.getFunction(s2)
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
        
    @staticmethod
    def showMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    
        def draw(self, context):
            self.layout.label(message)
    
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

    @staticmethod
    def displayErrors(errors):
        if errors:
            for _ in range(20):print()
            print("CTC Import Errors:")
            print("#"*75)
            print(errors)
            print("#"*75)
            ExportCCL.showMessageBox("Warnings have been Raised, check them in Window > Toggle_System_Console", title = "Warnings and Error Log")
        
    
def menu_func_export(self, context):
    self.layout.operator(ExportCCL.bl_idname, text="MHW CCL (.ccl)")
