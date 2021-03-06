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
from ..operators.ccltools import getCol,checkIsRoot
from ..operators.ctctools import checkIsChain, checkIsNode, checkIsChainStart, checkIsCTC, getStarFrame, accessScale

def isArray(propType):
    return "[" in propType and "char" not in propType

def blendToObj(obj,clss):
    #if renameScheme in clss
    dicObj = {}
    for prop in clss.fields:
        bprop = prop
        if hasattr(clss,"renameScheme"):
            if prop in clss.renameScheme:
                bprop = clss.renameScheme[prop]
        if isArray(clss.fields[prop]):
            if bprop+"000" in obj:
                listing = []
                ix = 0
                while (True):
                    try:
                        listing.append(obj[bprop+"%03d"%(ix)])
                        ix+=1
                    except:
                        break
                dicObj[prop] = listing
        else:
            if bprop in obj:
                dicObj[prop] = obj[bprop]
    return dicObj
            

class ExportCTC(Operator, ExportHelper):
    bl_idname = "custom_export.export_mhw_ctc"
    bl_label = "Save MHW CTC file (.ctc)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ctc"
    filter_glob = StringProperty(default="*.ctc", options={'HIDDEN'}, maxlen=255)

    missingFunctionBehaviour = EnumProperty(
            name = "Missing Bone Functions",
            description = "Determines what to do while opening a file with missing bone functions",
            items = [("Abort","Abort","Aborts exporting process",0),
                     ("Truncate","Truncate","Truncates the chain up to the offending node",1),
                     ("Dummy","Dummy","Sets the bone function to 255 and continues creating the chain",2)],
            default = "Truncate"
            )    

    @staticmethod
    def measureChain(chain):
        if not checkIsChain(chain):
            raise ValueError("Passed non-chain object %s"%chain.name)
        count = 0
        current = [obj for obj in chain.children if checkIsNode(obj)]
        while current:
            if len(current)>1:
                raise ValueError("Forked chain not under specification %s"%chain.name)
            current = [obj for obj in current[0].children if checkIsNode(obj)]
            count += 1
        return count
    
    @staticmethod
    def countChains(header):
        counting = 0
        for c in header.children:
            if checkIsChain(c): 
                counting += 1
        return counting
    
    def getFile(self):
        candidates = [obj for obj in bpy.context.scene.objects if checkIsCTC(obj)]
        if len(candidates) != 1:
            self.errors.append("Invalid number of ctc roots: %d"%len(candidates))
            raise ValueError()
        ctcf = candidates[0]
        fileHead = blendToObj(ctcf,Header)
        #fileHead["unknownsConstantIntSet"] = [candidates[0]["unknownsConstantIntSet%d"%i] for i in range(3)]
        #fileHead["unknownFloatSet"] = [candidates[0]["unknownFloatSet%d"%i] for i in range(3)]        
        fileHead["numARecords"] = self.countChains(ctcf)
        fileHead["numBRecords"] = sum((ExportCTC.measureChain(chain) for chain in ctcf.children))
        return Header().construct(fileHead),ctcf
        
    @staticmethod
    def getChains(file):
        candidates = [obj for obj in file.children if checkIsChain(obj)]
        chains = []
        for chain in candidates:
            arecord = blendToObj(chain,ARecord)     
            #("unknownByteSet","byte[2]"),("unknownByteSetCont","byte[12]"),
            #arecord["unknownByteSet"] = [chain["{Unknown Bytes %02d}"%i] for i in range(2)]
            #arecord["unknownByteSetCont"]  = [chain["{Unknown Bytes %02d}"%i] for i in range(2,14)]
            arecord["chainLength"] = ExportCTC.measureChain(chain)
            chains.append(ARecord().construct(arecord))
        return chains, candidates
    
    def chainToNodes(self, parent):
        current = [obj for obj in parent.children if checkIsNode(obj)]
        if not current:
            return []
        else:
            if len(current)>1:
                raise ValueError("Forked chain not under specification %s"%parent.name)
            currentNode = current[0]
            if not checkIsNode(currentNode):
                raise ValueError("Non-node object on chain %s"%currentNode.name)
            star = getStarFrame(currentNode)
            if star is None:
                raise ValueError("Node %s is missing it's corresponding * Frame"%currentNode.name)
            brecord = blendToObj(star,BRecord)
            brecord["Matrix"] = star.matrix_local.normalized()
            brecord["radius"] = star.empty_draw_size*accessScale(star.matrix_world.to_scale())
            #brecord["unknownFloatSet"] = [currentNode["UnknownFloat%02d"%i] for i in range(2)]
            #brecord["unknownByteSetTwo"] = [currentNode["UnknownByte%02d"%i] for i in range(5)]
            #brecord["isChainParent"] = checkIsChain(parent)
            try: 
                target = boneFunction = currentNode.constraints["Bone Function"].target
                if "boneFunction" in target: boneFunction = target["boneFunction"]
                elif checkIsRoot(target): boneFunction = -1
                else: raise
            except:
                self.errors.append("Missing Bone Function on Node %s"%currentNode.name)
                if self.missingFunctionBehaviour == "Abort": raise ValueError()
                if self.missingFunctionBehaviour == "Truncate": return []
                if self.missingFunctionBehaviour == "Dummy": boneFunction = 255
            brecord["boneFunctionID"] = boneFunction
            #"unknownByteSetTwo","byte[5]"
            return [BRecord().construct(brecord)]+self.chainToNodes(currentNode)
        
    def execute(self,context):
        self.errors = []
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        try: header,file = self.getFile()
        except ValueError: 
            self.displayErrors(self.errors)
            return {'CANCELLED'}
        arecords,chains = self.getChains(file)
        try: brecords = sum([self.chainToNodes(chain) for chain in chains],[])
        except ValueError: 
            self.displayErrors(self.errors)
            return {'CANCELLED'}
        binfile = Ctc().construct(header,arecords,brecords).serialize()
        with open(self.properties.filepath,"wb") as output:
            output.write(binfile)
        return {'FINISHED'}
    
    @staticmethod
    def showMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    
        def draw(self, context):
            self.layout.label(message)
    
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

    @staticmethod
    def displayErrors(errors):
        if errors:
            for _ in range(20):print()
            print("CTC Export Errors:")
            print("#"*75)
            print(errors)
            print("#"*75)
            ExportCTC.showMessageBox("Warnings have been Raised, check them in Window > Toggle_System_Console", title = "Warnings and Error Log")
    
    
def menu_func_export(self, context):
    self.layout.operator(ExportCTC.bl_idname, text="MHW CTC (.ctc)")
