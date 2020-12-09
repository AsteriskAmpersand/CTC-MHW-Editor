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

    missingFunctionBehaviour = EnumProperty(
            name = "Missing Bone Functions",
            description = "Determines what to do while opening a file with missing bone functions",
            items = [("Abort","Abort","Aborts importing process",0),
                     ("Omit","Omit","Omit the entire sphere",1),
                     ("Null","Null","Sets the constraint target to null",2)],
            default = "Null"
            )    
    
    def cleanup(self,obj):
        for children in obj.children:
            self.cleanup(children)
        objs = bpy.data.objects
        objs.remove(objs[obj.name], do_unlink=True)

    @staticmethod
    def showMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    
        def draw(self, context):
            self.layout.label(message)
    
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

    def displayErrors(self, errors):
        if errors:
            for _ in range(20):print()
            print("CCL Import Errors:")
            print("#"*75)
            print(errors)
            print("#"*75)
            if self.missingFunctionBehaviour == "Abort": message= "Import Process aborted due to error, check the reason in Window > Toggle_System_Console"
            else: message="Warnings have been Raised, check them in Window > Toggle_System_Console"
            self.showMessageBox(message, title = "Warnings and Error Log")
    
    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        self.ErrorMessages = []
        bpy.ops.object.select_all(action='DESELECT')
        try: ccl = CclFile(self.properties.filepath)
        except:
            self.ErrorMessages.append("Corrupted CCL File couldn't be read.")
            self.missingFunctionBehaviour = "Abort"
            self.displayErrors(self.ErrorMessages)
            return {'FINISHED'}
        capsules = []
        for ix, entry in enumerate(ccl.data):
            try:
                capsule = self.recordToCapsule(entry)
                capsule.name = "%d Capsule"%ix  
                capsules.append(capsule)
            except Exception as e:                
                if self.missingFunctionBehaviour == "Omit":
                    self.ErrorMessages.append("Warning %s"%e)
                    pass
                elif self.missingFunctionBehaviour == "Abort":
                    self.ErrorMessages.append("Error %s"%e)
                    for capsule in capsules: self.cleanup(capsule)
                    break
        self.displayErrors(self.ErrorMessages)
        return {'FINISHED'}

    def recordToCapsule(self, record):
        r1,co1 = record.startsphere_radius*self.scale, Vector([record.startsphere_xOffset, 
                                                    record.startsphere_yOffset, 
                                                    record.startsphere_zOffset])
        r2,co2 = record.endsphere_radius*self.scale, Vector([record.endsphere_xOffset,
                                                  record.endsphere_yOffset, 
                                                  record.endsphere_zOffset])
        try: f1 = findFunction(record.boneIDOne)
        except:
            self.ErrorMessages.append("CCL Points to Bone Function %d but missing from the Skeleton."%record.boneIDOne)
            if self.missingFunctionBehaviour == "Null": f1=None 
            else: raise ValueError()
        try: f2 = findFunction(record.boneIDTwo)
        except: 
            self.ErrorMessages.append("CCL Points to Bone Function %d but missing from the Skeleton."%record.boneIDTwo)
            if self.missingFunctionBehaviour == "Null": f1=None 
            else: raise ValueError()
        return createCapsule(f1,f2,r1,r2,co1,co2,record.unknownFrontBytesCont+record.unknownEndBytes)
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportCCL.bl_idname, text="MHW CCL (.ccl)")
