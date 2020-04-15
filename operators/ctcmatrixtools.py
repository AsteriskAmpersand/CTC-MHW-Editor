# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 00:53:55 2019

@author: AsteriskAmpersand
"""

import bpy
from mathutils import Vector, Matrix
from .ctctools import checkIsNode, checkIsChain

class ctcBase(bpy.types.Operator):
    bl_idname = 'ctc_tools.ctc_base'
    bl_label = 'CTC Base Operator'
    bl_options = {'INTERNAL'}
    addon_key = __package__.split('.')[0]
    def __init__(self):
        self.addon = bpy.context.user_preferences.addons[self.addon_key]        
    def execute (self, context):
        return self.core_operator(context)

class ctcNodeBase(ctcBase):
    bl_idname = 'ctc_tools.ctc_node_base'
    bl_label = 'CTC Node Base Operator'
    bl_options = {'INTERNAL'}
    addon_key = __package__.split('.')[0]
    @classmethod
    def poll(cls, context):
        obj_curr = context.active_object
        return obj_curr and checkIsNode(obj_curr)
    
class ctcChainBase(ctcBase):
    bl_idname = 'ctc_tools.ctc_chain_base'
    bl_label = 'CTC Node Chain Operator'
    bl_options = {'INTERNAL'}
    addon_key = __package__.split('.')[0]
    @classmethod
    def poll(cls, context):
        obj_curr = context.active_object
        return obj_curr and checkIsChain(obj_curr)    

class ctcGet(ctcNodeBase):
    @classmethod
    def poll(cls, context):
        selection = context.selected_objects
        return (
            super().poll(context) and
            (len(selection)==1)
        )
    def core_operator(self, context):
        self.addon.preferences.__setattr__(self.buffer,self.getProperty(context.active_object))
        return {'FINISHED'}
        
class ctcSet(ctcNodeBase):
    @classmethod
    def poll(cls, context):
        # Exactly one vertex or face must be selected.
        selection = context.selected_objects
        return (
            super().poll(context) and
            all([checkIsNode(obj) for obj in selection])
        )
    def core_operator(self, context):
        for obj in context.selected_objects:
            self.setProperty(obj, self.addon.preferences.__getattribute__(self.buffer))
        return {'FINISHED'}
    
class get_all_matrices(ctcGet):
    bl_idname = 'ctc_tools.get_all_matrices'
    bl_label = 'Get Node Matrices'
    bl_description = 'Copy selected node matrices.'
    buffer = 'matrices_buffer'

    def getProperty(self,obj):
        self.addon.preferences.rotation_buffer = Matrix(obj["Matrix"]).to_euler()
        self.addon.preferences.translation_buffer = Matrix(obj["Matrix"]).to_translation()
        self.addon.preferences.unknown_floats_buffer = [obj["UnknownFloat%02d"%i] for i in range(2)]
        self.addon.preferences.unknown_bytes_buffer_l = [obj["UnknownByte%02d"%i] for i in range(3)]
        self.addon.preferences.unknown_bytes_buffer_r = [obj["UnknownByte%02d"%i] for i in range(3,5)]
        self.addon.preferences.unknown_bytes_buffer = [obj["UnknownByte%02d"%i] for i in range(5)]
        return {key:obj[key] for key in obj.keys()}
    
class set_all_matrices(ctcSet):
    bl_idname = 'ctc_tools.set_all_matrices'
    bl_label = 'Set Node Matrices'
    bl_description = 'Paste selected node matrices.'
    buffer = 'matrices_buffer'
    @staticmethod
    def setProperty(obj,value):
        for key in value:
            obj[key]=value[key]
    
    
class get_rotation_matrices(ctcGet):
    bl_idname = 'ctc_tools.get_rotation_matrices'
    bl_label = 'Get Node Rotation Matrices'
    bl_description = 'Copy selected node rotation matrix.'
    buffer = 'rotation_buffer'
    @staticmethod
    def getProperty(obj):
        return Matrix(obj["Matrix"]).to_euler()
     
class set_rotation_matrices(ctcSet):
    bl_idname = 'ctc_tools.set_rotation_matrices'
    bl_label = 'Set Node Rotation Matrices'
    bl_description = 'Paste selected node rotation matrix.'
    buffer = 'rotation_buffer'
    @staticmethod
    def setProperty(obj,value):
        obj["Matrix"] = Matrix.Translation(Matrix(obj["Matrix"]).to_translation() )*value.to_matrix().to_4x4()
        
class get_translation_matrices(ctcGet):
    bl_idname = 'ctc_tools.get_translation_matrices'
    bl_label = 'Get Node Translation Matrices'
    bl_description = 'Copy selected node translation matrix.'
    buffer = 'translation_buffer'
    @staticmethod
    def getProperty(obj):
        return Matrix(obj["Matrix"]).to_translation()
      
class set_translation_matrices(ctcSet):
    bl_idname = 'ctc_tools.set_translation_matrices'
    bl_label = 'Set Node Translation Matrices'
    bl_description = 'Paste selected node translation matrix.'
    buffer = 'translation_buffer'
    @staticmethod
    def setProperty(obj,value):
        rot = Matrix(obj["Matrix"]) - Matrix.Translation(Matrix(obj["Matrix"]).to_translation())
        puretrans = Matrix.Translation(value) - Matrix.Identity(4)
        obj["Matrix"] =  rot + puretrans
        
class get_unknowns(ctcGet):
    bl_idname = 'ctc_tools.get_unknowns'
    bl_label = 'Get Node Unknowns'
    bl_description = 'Copy selected node unknowns.'
    bytebuffer = 'unknown_bytes_buffer'
    floatbuffer = 'unknown_floats_buffer'
    def core_operator(self, context):
        prop = self.getByteProperty(context.active_object)
        l,r = prop[:3],prop[3:5]
        for ix,v in enumerate(l):self.addon.preferences.__getattribute__(self.bytebuffer+"_l")[ix] = v
        for ix,v in enumerate(r):self.addon.preferences.__getattribute__(self.bytebuffer+"_r")[ix] = v
        for ix,v in enumerate(self.getFloatProperty(context.active_object)):
            self.addon.preferences.__getattribute__(self.floatbuffer)[ix] = v
        return {'FINISHED'}
    @staticmethod
    def getByteProperty(obj):
        return [obj["UnknownByte%02d"%i] for i in range(5)]
    @staticmethod
    def getFloatProperty(obj):
        return [obj["UnknownFloat%02d"%i] for i in range(2)]
      
class set_unknowns(ctcSet):
    bl_idname = 'ctc_tools.set_unknowns'
    bl_label = 'Set Node Unknown Bytes'
    bl_description = 'Paste selected node unknown bytes.'
    bytebuffer = 'unknown_bytes_buffer'
    floatbuffer = 'unknown_floats_buffer'
    def core_operator(self, context):
        for obj in context.selected_objects:
            self.setProperty(obj, 
                             list(self.addon.preferences.__getattribute__(self.bytebuffer+"_l"))+
                             list(self.addon.preferences.__getattribute__(self.bytebuffer+"_r")),
                             self.addon.preferences.__getattribute__(self.floatbuffer))
        return {'FINISHED'}    
    @staticmethod
    def setProperty(obj,bytevalue,floatvalue):
        for i in range(5):
            obj["UnknownByte%02d"%i] = bytevalue[i]
        for i in range(2):
            obj["UnknownFloat%02d"%i] = floatvalue[i]      
            
class get_chain_data(ctcChainBase):
    bl_idname = 'ctc_tools.get_chain_data'
    bl_label = 'Get Chain Data'
    bl_description = 'Copy selected node matrices.'
    buffer = 'chain_buffer'
    @classmethod
    def poll(cls, context):
        # Exactly one vertex or face must be selected.
        selection = context.selected_objects
        return (
            super().poll(context) and
            (len(selection)==1)
        )
    def core_operator(self, context):
        self.addon.preferences.__setattr__(self.buffer,self.getProperty(context.active_object))
        return {'FINISHED'}
    @staticmethod
    def getProperty(obj):
        return {k:obj[k] for k in obj.keys()}
    
class set_chain_data(ctcChainBase):
    bl_idname = 'ctc_tools.set_chain_data'
    bl_label = 'Set Chain Data'
    bl_description = 'Paste selected node matrices.'
    buffer = 'chain_buffer'
    @classmethod
    def poll(cls, context):
        # Exactly one vertex or face must be selected.
        selection = context.selected_objects
        return (
            super().poll(context) and
            all([checkIsChain(obj) for obj in selection])
        )
    def core_operator(self, context):
        for obj in context.selected_objects:
            self.setProperty(obj, self.addon.preferences.__getattribute__(self.buffer))
        return {'FINISHED'}
    @staticmethod
    def setProperty(obj,value):
        for key in value:
            obj[key] = value[key]
    
