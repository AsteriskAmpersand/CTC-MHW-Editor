# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 14:09:29 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator



class ImportCTC(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ctc"
    bl_label = "Load MHW CTC file (.ctc)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ctc"
    filter_glob = StringProperty(default="*.ctc", options={'HIDDEN'}, maxlen=255)
    
    """
    clear_scene = BoolProperty(
        name = "Clear scene before import.",
        description = "Clears all contents before importing",
        default = True)
    maximize_clipping = BoolProperty(
        name = "Maximizes clipping distance.",
        description = "Maximizes clipping distance to be able to see all of the model at once.",
        default = True)"""

    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportCTC.bl_idname, text="MHW CTC (.ctc)")
