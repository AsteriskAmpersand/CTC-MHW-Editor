# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 14:09:29 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from ..structures.Ctc import CtcFile
from ..operators.ccltools import findFunction
from ..operators.ctctools import createCTCHeader, createChain

class ImportCTC(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ctc"
    bl_label = "Load MHW CTC file (.ctc)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ctc"
    filter_glob = StringProperty(default="*.ctc", options={'HIDDEN'}, maxlen=255)
    
    scale = BoolProperty(
        name = "Delete Incomplete Chains" ,
        description = "Delete nodes with missing bone functions.",
        default = False)    
    
    @staticmethod
    def breakHeader(header):
        return (header.unknownsConstantIntSet,
                header.unknownConstantInt,
                header.updateTicks,
                header.poseSnapping,
                header.chainDamping,
                header.reactionSpeed,
                header.gravityMult,
                header.windMultMid,
                header.windMultLow,
                header.windMultHigh,
                header.unknownFloatSet)
        
    @staticmethod
    def breakChainHeader(chain):
        return (chain.collision,
                chain.weightiness,
                chain.unknownByteSet + chain.unknownByteSetCont,
                chain.xGravity,
                chain.yGravity,
                chain.zGravity,
                chain.xInertia,
                chain.yInertia,
                chain.zInertia,
                chain.unknownFloatTwo,
                chain.unknownFloatThree,
                chain.unknownFloatFour,
                chain.windMultiplier,
                chain.lod)
        
    @staticmethod
    def createRecordNode(node):
        rootco = findFunction(node.boneFunctionID)
        o = bpy.data.objects.new("CtcNode", None )
        bpy.context.scene.objects.link( o )
        mod = o.constraints.new(type = "CHILD_OF")#name= "Bone Function"
        mod.name = "Bone Function"
        mod.target = rootco
        #mod.inverse_matrix = node.matrix #experiment into the meaning of the matrix
        o["Type"] = "CTC_Node"
        o.empty_draw_size = .5
        o.empty_draw_type = "SPHERE"
        o.show_x_ray = True
        o.show_bounds = False
        for i in range(5):
            o["UnknownByte%02d"%i] = node.unknownByteSetTwo[i]
        o["Vector"] = node.Vector
        o["Matrix"] = node.Matrix
        result = o
        return result

    @staticmethod
    def createRecordChain(chain):
        chainmeta = createChain(*ImportCTC.breakChainHeader(chain.chain))
        parent = chainmeta
        for node in chain:
            node = ImportCTC.createRecordNode(node)
            node.parent = parent
            bpy.context.scene.update()
            node.constraints["Bone Function"].inverse_matrix = parent.matrix_world.inverted()
            parent = node
        return chainmeta
        
    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        ctc = CtcFile(self.properties.filepath).data
        header = ctc.Header
        ctchead = createCTCHeader(*self.breakHeader(header))
        for chain in ctc:
            ctcchain = self.createRecordChain(chain)
            ctcchain.parent = ctchead
        return {'FINISHED'}
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportCTC.bl_idname, text="MHW CTC (.ctc)")
