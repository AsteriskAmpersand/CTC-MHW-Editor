# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 00:22:42 2019

@author: AsteriskAmpersand
"""

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from mathutils import Vector, Matrix
from ..structures.Ctc import Ctc,Header,ARecord,BRecord
from ..operators.ccltools import getCol

class ExportCTC(Operator, ExportHelper):
    bl_idname = "custom_export.export_mhw_ctc"
    bl_label = "Save MHW CTC file (.ctc)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ccl"
    filter_glob = StringProperty(default="*.ctc", options={'HIDDEN'}, maxlen=255)
    
    @staticmethod
    def measureChain(chain):
        if chain.type != "EMPTY" or "Type" not in chain or chain["Type"]!="CTC_Chain":
            raise ValueError("Passed non-chain object %s"%chain.name)
        count = 0
        current = [obj for obj in chain.children if obj.type == "EMPTY" and "Type" in obj and obj["Type"]=="CTC_Node"]
        while current:
            if len(current)>1:
                raise ValueError("Forked chain not under specification %s"%chain.name)
            current = [obj for obj in current[0].children if obj.type == "EMPTY" and "Type" in obj and obj["Type"]=="CTC_Node"]
            count += 1
        return count
            
    
    @staticmethod
    def getFile():
        candidates = [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY" and "Type" in obj and obj["Type"]=="CTC"]
        if len(candidates) != 1:
            raise ValueError("Invalid number of ctc roots: %d"%len(candidates))
        fileHead = {key:candidates[0][key] for key in candidates[0].keys() if key in Header.fields}
        fileHead["unknownsConstantIntSet"] = [candidates[0]["unknownsConstantIntSet%d"%i] for i in range(3)]
        fileHead["unknownFloatSet"] = [candidates[0]["unknownFloatSet%d"%i] for i in range(3)]        
        fileHead["numARecords"] = len(candidates[0].children)
        fileHead["numBRecords"] = sum((ExportCTC.measureChain(chain) for chain in candidates[0].children))
        return Header().construct(fileHead),candidates[0]
        
    @staticmethod
    def getChains(file):
        candidates = [obj for obj in file.children if obj.type == "EMPTY" and "Type" in obj and obj["Type"]=="CTC_Chain"]
        chains = []
        for chain in candidates:
            arecord = {key:chain[key] for key in chain.keys() if key in ARecord.fields}
            #("unknownByteSet","byte[2]"),("unknownByteSetCont","byte[12]"),
            arecord["unknownByteSet"] = [chain["unknownBytes%02d"%i] for i in range(2)]
            arecord["unknownByteSetCont"]  = [chain["unknownBytes%02d"%i] for i in range(2,14)]
            arecord["chainLength"] = ExportCTC.measureChain(chain)
            chains.append(ARecord().construct(arecord))
        return chains, candidates
    
    @staticmethod
    def chainToNodes(chain):
        current = [obj for obj in chain.children if obj.type == "EMPTY" and "Type" in obj and obj["Type"]=="CTC_Node"]
        if not current:
            return []
        else:
            if len(current)>1:
                raise ValueError("Forked chain not under specification %s"%chain.name)
            currentNode = current[0]
            if currentNode.type != "EMPTY" or "Type" not in currentNode or currentNode["Type"]!="CTC_Node":
                raise ValueError("Non-node object on chain %s"%currentNode.name)
            brecord = {key:currentNode[key] for key in currentNode.keys() if key in BRecord.fields}
            brecord["Matrix"] = Matrix(currentNode["Matrix"])
            brecord["Vector"] = Vector(currentNode["Vector"])
            brecord["unknownByteSetTwo"] = [currentNode["UnknownByte%02d"%i] for i in range(5)]
            brecord["isChainParent"] = "Type" in chain and chain["Type"]=="CTC_Chain"
            brecord["boneFunctionID"] = currentNode.constraints["Bone Function"].target["boneFunction"]
            #"unknownByteSetTwo","byte[5]"
            return [BRecord().construct(brecord)]+ExportCTC.chainToNodes(currentNode)
        
    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        header,file = self.getFile()
        arecords,chains = self.getChains(file)
        brecords = sum([self.chainToNodes(chain) for chain in chains],[])
        binfile = Ctc().construct(header,arecords,brecords).serialize()
        with open(self.properties.filepath,"wb") as output:
            output.write(binfile)
        return {'FINISHED'}
    
def menu_func_export(self, context):
    self.layout.operator(ExportCTC.bl_idname, text="MHW CTC (.ctc)")
