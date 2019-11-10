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
from ..operators.ctctools import createCTCHeader, createChain, createCTCNode

class ImportCTC(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ctc"
    bl_label = "Load MHW CTC file (.ctc)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ctc"
    filter_glob = StringProperty(default="*.ctc", options={'HIDDEN'}, maxlen=255)
    
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
        try:
            rootco = findFunction(node.boneFunctionID)
        except:
            rootco = None
        return createCTCNode(rootco,node.unknownByteSetTwo,node.Vector,node.Matrix)

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
