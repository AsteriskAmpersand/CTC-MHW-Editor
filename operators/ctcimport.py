# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 14:09:29 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from ..structures.Ctc import CtcFile, Header, ARecord, BRecord
from ..operators.ccltools import findFunction
from ..operators.ctctools import createCTCHeader, createChain, createCTCNode

class BoneFunctionError(Exception):
    pass

class LoadError(Exception):
    pass

class ImportCTC(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ctc"
    bl_label = "Load MHW CTC file (.ctc)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ctc"
    filter_glob = StringProperty(default="*.ctc", options={'HIDDEN'}, maxlen=255)
       
    missingFunctionBehaviour = EnumProperty(
            name = "Missing Bone Functions",
            description = "Determines what to do while opening a file with missing bone functions",
            items = [("Abort","Abort","Aborts importing process",0),
                     ("Truncate","Truncate","Truncates the chain up to the offending node",1),
                     ("Null","Null","Sets the constraint target to null and continues creating the chain",2)],
            default = "Null"
            )    
    
    @staticmethod
    def breakObj(obj,clss):
        return [(obj.renameScheme[prop] if hasattr(obj,"renameScheme") and prop in obj.renameScheme else prop,
                 getattr(obj,prop))
                for prop in clss.fields]# if prop not in clss.hide
    
    @staticmethod
    def breakHeader(header):
        return ImportCTC.breakObj(header,Header)
        
    @staticmethod
    def breakChainHeader(chain):
        return ImportCTC.breakObj(chain,ARecord)
        
    @staticmethod
    def breakNode(node):
        return ImportCTC.breakObj(node,BRecord)
    
    def createRecordNode(self, node):
        missingFunction = False
        try:
            rootco = findFunction(node.boneFunctionID)
        except:
            rootco = None
            missingFunction = True
        result = createCTCNode(rootco,node.radius,node.Matrix,*ImportCTC.breakNode(node))
        
        if missingFunction:
            if self.missingFunctionBehaviour == "Abort":
                self.Abort = True
            if self.missingFunctionBehaviour == "Truncate" or self.missingFunctionBehaviour == "Abort":
                self.ErrorMessages.append("A chain depends on bone function %d which can't be found in the skeleton."%
                          (node.boneFunctionID))
                raise BoneFunctionError() 
            else:
                self.ErrorMessages.append("%s pointed to bone function %d which couldn't be found in the skeleton."%
                          (result.name,node.boneFunctionID))
        return result

    def createRecordChain(self, chain):
        chainmeta = createChain(*self.breakChainHeader(chain.chain))
        parent = chainmeta
        for node in chain:
            try:
                node = self.createRecordNode(node)
                node.parent = parent
                bpy.context.scene.update()
                #if node["Fixed End"]:
                node.constraints["Bone Function"].inverse_matrix = parent.matrix_world.inverted()
                bpy.context.scene.update()
                parent = node
            except BoneFunctionError:
                break
        return chainmeta
    
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

    @staticmethod
    def displayErrors(errors):
        if errors:
            for _ in range(20):print()
            print("CTC Import Errors:")
            print("#"*75)
            print(errors)
            print("#"*75)
            ImportCTC.showMessageBox("Warnings have been Raised, check them in Window > Toggle_System_Console", title = "Warnings and Error Log")
    
    def loadCtc(self, filename):
        try:
            fileContents = CtcFile(filename).data
        except:
            self.ErrorMessages.append("Corrupted CTC can't be loaded.")
            raise LoadError()
        return fileContents
    
    def execute(self,context):
        self.Abort = False
        self.ErrorMessages = []
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        try:
            ctc = self.loadCtc(self.properties.filepath)
        except LoadError:
            self.displayErrors(self.ErrorMessages)
            return {'FINISHED'}
        header = ctc.Header
        ctchead = createCTCHeader(*self.breakHeader(header))
        for chain in ctc:
            ctcchain = self.createRecordChain(chain)
            ctcchain.parent = ctchead
            if self.Abort:
                self.cleanup(ctchead)
                break
        bpy.context.scene.update()
        self.displayErrors('\r\n'.join(self.ErrorMessages))
        return {'FINISHED'}
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportCTC.bl_idname, text="MHW CTC (.ctc)")
