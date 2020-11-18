# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 23:04:20 2019

@author: AsteriskAmpersand
"""

"""
import selection_utils

selection_utils.selected #selection in order
"""
import bpy
from mathutils import Vector, Matrix
from bpy.props import IntProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty, PointerProperty
from ..operators.ccltools import findFunction,checkSubStarType,checkStarType,checkIsStarType
from ..structures.Ctc import ARecord,BRecord,Header
import os
import json
import copy
accessScale = lambda scaleVector: scaleVector[0]

    
def rename(tuples,clss):
    return [(clss.renameScheme[prop] if hasattr(clss,"renameScheme") and prop in clss.renameScheme else prop,val)
            for prop,val in tuples]# if prop not in clss.hide

def breakObj(obj,clss):
    return [(obj.renameScheme[prop] if hasattr(obj,"renameScheme") and prop in obj.renameScheme else prop,
             getattr(obj,prop))
            for prop in clss.fields]# if prop not in clss.hide


def breakHeader(header):
    return breakObj(header,Header)
    

def breakChainHeader(chain):
    return breakObj(chain,ARecord)
    

def breakNode(node):
    return breakObj(node,BRecord)

def writeProp(obj,propName,prop):
    try:
        if type(prop) is str:
            raise ValueError
        iter(prop)
        fromArray(obj,propName,prop)
    except:
        fromSingle(obj,propName,prop)

def fromSingle(obj,propName,prop):
    obj[propName] = prop

def fromArray(obj, propName, array):
    for i,propPoint in enumerate(array):
        obj[propName+"%03d"%i]=propPoint

chainPresets = []
presetSize = 0

class PresetLoop():
    def __init__(self,listing):
        self.cur = 0
        self.listing = listing
    def __next__(self):
        item = self.listing[self.cur]
        if self.cur+1 < len(self.listing):self.cur += 1
        return item

class CTCPreset():
    def __init__(self,preset_obj):
        self.file_header = preset_obj["file_header"]
        self.chain_definition = preset_obj["chain_header"]
        self.display_name = preset_obj["name"]
        self.description = preset_obj["description"] if "description" in preset_obj else "Ctc Preset"
        self.parent = int(preset_obj["parent"])
        self.allNodes = preset_obj["nodes"]
    def name(self):
        return self.display_name
    def enumDisplay(self):
        return (self.name(),self.name(),self.description)
    def rootID(self): return self.parent
    def bodyNodes(self):return self.allNodes[:-1]
    def endNode(self):return self.allNodes[-1]
    def __iter__(self):
        return PresetLoop(self.bodyNodes())
    
currentPresetSize = 0
script_file = os.path.realpath(__file__)
directory =  os.path.dirname(os.path.dirname(script_file))
presetFile = directory+"\\"+"CTCPresets.json"
def initializePresets():
    global currentPresetSize
    presets = []
    if os.path.exists(presetFile):
        file = open(presetFile,"r")
        presets = [CTCPreset(preset) for preset in json.load(file)["presets"]]
        presets = {p.name():p for p in sorted(presets,key=lambda x: x.name())}
        currentPresetSize = os.stat(presetFile).st_size
    return presets
    
preset = initializePresets()
def getPresets(ctx,obj,*args,**kwargs):
    if os.path.exists(presetFile):
        global currentPresetSize 
        size = os.stat(presetFile).st_size
        if currentPresetSize != size:
            global preset
            preset = initializePresets()
            currentPresetSize = size
    return [p.enumDisplay() for p in preset.values()]
    #print (preset)

def findPreset(presetString):
    return preset[presetString]

def createCTCHeader(*args):
    header = bpy.data.objects.new("CtcHeader", None )
    bpy.context.scene.objects.link( header )
    #mod.inverse_matrix = node.matrix #experiment into the meaning of the matrix
    header.empty_draw_size = 0
    header.empty_draw_type = "SPHERE"
    header.show_x_ray = True
    for name,prop in args:
        writeProp(header,name,prop)
    header["Type"] = "CTC"
    return header

def createChain(*args):
    chain = bpy.data.objects.new("CtcChain", None )
    bpy.context.scene.objects.link( chain )
    chain["Type"] = "CTC_Chain"
    chain.empty_draw_size = .75
    chain.empty_draw_type = "CIRCLE"
    chain.show_x_ray = True
    for name,prop in args:
        writeProp(chain,name,prop)
    return chain

def createStarFrame(obj,radius,mat):
    o = bpy.data.objects.new("*Frame", None )
    bpy.context.scene.objects.link( o )
    o.parent = obj
    o.matrix_world = mat
    o.empty_draw_type = "ARROWS"
    o.show_x_ray = True
    o.show_bounds = False
    o["Type"] = "CTC_*_Frame"
    o.empty_draw_size = obj.empty_draw_size
    return o

def createCTCNode(rootco, rad, mat, *args):
        o = bpy.data.objects.new("CtcNode", None )
        bpy.context.scene.objects.link( o )
        #o.matrix_world = mat
        mod = o.constraints.new(type = "CHILD_OF")#name= "Bone Function"
        mod.name = "Bone Function"
        mod.target = rootco
        #mod.inverse_matrix = node.matrix #experiment into the meaning of the matrix
        o["Type"] = "CTC_Node"
        #o.empty_draw_size = rad
        o.empty_draw_type = "SPHERE"
        o.show_x_ray = True
        o.show_bounds = False
        o.hide_select = True
        f = createStarFrame(o,rad,mat)
        for name,prop in args:
            writeProp(f,name,prop)        
        #o["Matrix"] = mat
        #if not o["Fixed End"]:
        #    mod.mute = True
         #   o.location = rootco.location
        return o

def getChild(candidate):
    generator = (c for c in candidate.children if checkStarType("CTC_Node")(c))
    try: w = next(generator)
    except: return None
    try: next(generator)
    except: return w
    raise ValueError("Forked chain not under specification %s"%candidate.name)
    
def checkChildren(candidate):
    getChild(candidate)
    return True

checkIsSubCTC = checkSubStarType("CTC")
checkIsCTC = checkStarType("CTC")
checkIsChain = lambda x: checkStarType("CTC_Chain")(x) and checkChildren(x)
checkIsNode = lambda x: checkStarType("CTC_Node")(x) and checkChildren(x)
checkIsChainStart = lambda x:checkIsNode(x) and x.parent and checkIsChain(x.parent)
checkIsChainEnd = lambda x:checkIsNode(x) and len([w for w in x.children if checkIsNode(w)]) == 0
checkIsBone = lambda x: x and x.type == "EMPTY" and "boneFunction" in x

def getUpperChain(chainEnd):
    if chainEnd.parent and checkIsNode(chainEnd.parent) :
        return getUpperChain(chainEnd.parent) + [chainEnd]
    else:
        return [chainEnd]
    
def getLowerChain(chainStart):
    child = getChild(chainStart)
    if child:
        start = [] if checkIsChain(chainStart) else [chainStart]
        return start + getLowerChain(child)
    else:
        return [chainStart]
    
def getDescendantOrNone(bone):
    children = sorted([obj for obj in bone.children if checkIsBone(obj)],
                       key = lambda x: abs(int(x["boneFunction"])-bone["boneFunction"]))
    if children:
        return children[0]
    else: return None
    
def getChainEnd(active):
    child = getChild(active)
    if not child:
        if checkIsChain(active):
            raise ValueError("Chain has no nodactivees")
        return active
    else:
        return getChainEnd(child)
        
def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class createCTC(bpy.types.Operator):
    bl_idname = 'ctc_tools.create_ctc'
    bl_label = "Create CTC Header"
    bl_description = 'Create CTC Header'
    bl_options = {"REGISTER", "UNDO"}

    preset = EnumProperty(
        name = "Preset Properties",
        description = "Load a preset for chain properties.",
        items = getPresets,
        )    

    def execute(self,context):
        createCTCHeader(*findPreset(self.preset).file_header.items())
        return {"FINISHED"}
    
class chainFromSelection(bpy.types.Operator):        
    bl_idname = 'ctc_tools.chain_from_selection'
    bl_label = 'Create CTC Chain'
    bl_description = 'Create CTC Chain from Selection'
    bl_options = {"REGISTER", "UNDO"}

    preset = EnumProperty(
        name = "Preset Properties",
        description = "Load a preset for chain properties.",
        items = getPresets,
        )    
    @staticmethod
    def buildChain(selection, chainStart):
        chain = []
        parent = chainStart
        first = True
        for bone in bpy.selection:
            bprop = BRecord.defaultProperties
            if first:
                first = False
                bprop["fixedEnd"]=True
            node = createCTCNode(bone,1,Matrix.Identity(4),*bprop.items())
            node.parent = parent
            bpy.context.scene.update()
            node.constraints["Bone Function"].inverse_matrix = parent.matrix_world.inverted()
            parent = node
            chain.append(node)
        for (parent,nextParent),(node,nextNode) in zip(zip(bpy.selection,bpy.selection[1:]),zip(chain,chain[1:])):                                                         
            orientToActive.orientVectorSystem(node,nextParent,Vector([1,0,0]),parent)
        return chain
    
    @classmethod
    def poll(cls,context):
        selection = bpy.selection
        for bone in selection:
            if not checkIsBone(bone):
                return False
        return len(selection)>0
    
    def execute(self,context):
        selection = bpy.selection
        #self.validate(selection)
        preset = findPreset(self.preset)
        chainStart = createChain(*preset.chain_definition.items())
        chain = chainFromSelection.buildChain(selection,chainStart)
        applyPreset.applyPreset(chainStart,preset)
        return {"FINISHED"}
    
class nodeFromActive(bpy.types.Operator):        
    bl_idname = 'ctc_tools.node_from_active'
    bl_label = 'Create CTC Node'
    bl_description = 'Create CTC Node from Active'
    bl_options = {"REGISTER", "UNDO"}
    
    radius = FloatProperty(
        name = "Collision Radius",
        description = "Collision Radius.",
        default = 1.0
        )
    fixed = IntProperty(
        name = "Fixed End",
        description = "Determines if bone should be afixed to position (catenary end).",
        default = 0
        )
    ubst = EnumProperty(
        name = "Unknown Byte Set",
        description = "Set of Unknown Bytes",
        items = list(reversed([(str(entry),str(entry),"")
                for entry in [(0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (0, 0, 0, 1, 1),
                              (0, 0, 0, 2, 1), (0, 1, 0, 0, 0), (0, 1, 0, 0, 1),
                              (0, 1, 0, 0, 2), (0, 1, 0, 1, 0), (0, 1, 0, 1, 1),
                              (0, 1, 0, 1, 2), (0, 1, 0, 2, 0), (0, 1, 0, 2, 1),
                              (0, 1, 0, 2, 2), (0, 2, 0, 0, 0), (0, 2, 0, 0, 1),
                              (0, 2, 0, 1, 1), (0, 2, 0, 2, 1), (0, 2, 0, 2, 2),
                              (0, 3, 0, 0, 1), (0, 3, 0, 1, 1), (0, 3, 0, 2, 1),
                              (1, 1, 0, 1, 1)]
                ]))
        )
    unk50 = IntProperty(
        name = "Unknown 50",
        description = "Unknown that takes values between 54 and 59 or 0.",
        default = 0
        )
    unkFS0 = FloatProperty(
        name = "Unknown Float 0",
        description = "Unknown Float",
        default = 1.0
        )
    unkFS1 = FloatProperty(
        name = "Unknown Float 1",
        description = "Unknown Float",
        default = 1.0
        )
    unkFS2 = FloatProperty(
        name = "Unknown Float 2",
        description = "Unknown Float",
        default = 1.0
        )
    @classmethod
    def poll(cls,context):
        return bpy.context.active_object and "boneFunction" in bpy.context.active_object
    
    def execute(self,context):
        rootco = bpy.context.active_object
        bprop = BRecord.defaultProperties.copy()
        bprop["fixedEnd"] = self.fixed
        bprop["unknownByteSetTwo"] = eval(self.ubst)
        bprop["boneFunctionID"] = rootco["boneFunction"],
        bprop["unknown50"] = self.unk50
        bprop["radius"] = self.radius
        bprop["unknownFloatSet"] = [self.unkFS0,self.unkFS1,self.unkFS2]
        createCTCNode(rootco,self.radius,Matrix.Identity(4),*bprop.items())
        
        return {"FINISHED"}

def getRoot(currentNode):
    if "Bone Function" not in currentNode.constraints or \
        currentNode.constraints["Bone Function"].target is None or \
            "boneFunction" not in currentNode.constraints["Bone Function"].target:
                return None
    else: return currentNode.constraints["Bone Function"].target

checkIsStarFrame = checkStarType("CTC_*_Frame")

def getStarFrame(currentNode):
    for c in currentNode.children:
        if checkIsStarFrame(c):
            return c
    else: return None

def orientVectorPair(v0,v1):
    v0 = v0.normalized()
    v1 = v1.normalized()
    if v0 == v1:
        return Matrix.Identity(3)
    v = v0.cross(v1)
    #s = v.length
    c = v0.dot(v1)
    if c == -1: return Matrix([[-1,0,0],[0,-1,0],[0,0,1]])
    vx = Matrix([[0,-v[2], v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return Matrix.Identity(3)+vx+(1/(1+c))*vx*vx
    
class orientToActive(bpy.types.Operator):
    bl_idname = 'ctc_tools.orient_to_active'
    bl_label = 'Orient to Active'
    bl_description = 'Orient selection to active.'
    bl_options = {"REGISTER", "UNDO"}
    
    axis = EnumProperty(
        name = "Axis Vector",
        description = "Axis vector to align",
        items = list(reversed([("x","X-Axis","",0),
                 ("y","Y-Axis","",1),
                 ("z","Z-Axis","",2),])),
        default = "x"
        )
    
    @classmethod
    def poll(cls,context):
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        return active and selection and all(map(lambda x: (checkIsNode(x) and getStarFrame(x) is not None) or checkIsStarFrame(x),selection))
    
    @staticmethod
    def orientVectorSystem(obj,target,axis,origin = None):
        star = obj if checkIsStarFrame(obj) else getStarFrame(obj)
        if origin is None:
            origin = star
        sscale = star.empty_draw_size*accessScale(star.matrix_world.to_scale())
        star.empty_draw_size = sscale
        loc = star.location
        targetVector = target.matrix_world.translation-origin.matrix_world.translation
        M = orientVectorPair(axis,targetVector)
        star.matrix_local = M.to_4x4()
        star.location = loc
    
    def execute(self,context):
        vec = Vector({"x":[1,0,0],"y":[0,1,0],"z":[0,0,1]}[self.axis])
        active = bpy.context.active_object
        for obj in [obj for obj in bpy.context.selected_objects if obj != active]:
            self.orientVectorSystem(obj,active,vec)
        #bpy.context.scene.update()
        return {"FINISHED"}

class orientToActiveProjection(bpy.types.Operator):
    bl_idname = 'ctc_tools.orient_projection'
    bl_label = 'Orient to Active Projection'
    bl_description = 'Orient selection to active projection on the plane whose normal is the fixed vector.'
    bl_options = {"REGISTER", "UNDO"}
    
    axis = EnumProperty(
        name = "Fixed Vector - Orienting Vector",
        description = "Axis vector to freeze and vector to align",
        items = list(reversed([
                ('("x","y")',"Freeze X - Orient Y ","",0),
                ('("x","z")',"Freeze X - Orient Z ","",1),
                ('("y","x")',"Freeze Y - Orient X ","",2),
                ('("y","z")',"Freeze Y - Orient Z ","",3),
                ('("z","x")',"Freeze Z - Orient X ","",4),
                ('("z","y")',"Freeze Z - Orient Y ","",5),
                 ])),
        default = '("z","x")'
        )
        
    @classmethod
    def poll(cls,context):
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        return active and selection and all(map(lambda x: (checkIsNode(x) and getStarFrame(x) is not None) or checkIsStarFrame(x),selection))
    
    
    def orientVectorSystem(self, obj, target, frozenAxis, freeVector):
        star = obj if checkIsStarFrame(obj) else getStarFrame(obj)
        
        sscale = star.empty_draw_size*accessScale(star.matrix_world.to_scale())
        star.empty_draw_size = sscale
        mat = star.matrix_local.normalized()
        star.matrix_local.normalize()
        frozenAxis = Vector(mat.col[frozenAxis][0:3])
        freeVector = Vector(mat.col[freeVector][0:3])
        targetVector = (target.matrix_world.translation-star.matrix_world.translation).normalized()
        projection = self.normalProjection(frozenAxis,targetVector)
        if projection.length < 0.001: return
        M = orientVectorPair(freeVector,projection)
        loc = star.location
        star.matrix_local = M.to_4x4()*star.matrix_local
        star.location = loc
        return
        
        
    def normalProjection(self,normal,vector):
        return vector - vector.dot(normal)/normal.length**2*normal
    
    def execute(self,context):
        fix,orienting = eval(self.axis)
        active = bpy.context.active_object
        frozenIndex = {"x":0,"y":1,"z":2}[fix]
        freeIndex = {"x":0,"y":1,"z":2}[orienting]
        for obj in [obj for obj in bpy.context.selected_objects if obj != active]:
            self.orientVectorSystem(obj,active,frozenIndex,freeIndex)
        return {"FINISHED"}
            

def chainRematchValidate(active,selection):
    if len(selection) != 1:
        return False
    select = selection[0]
    if not(checkIsChain(select) or checkIsNode(select) or checkIsStarFrame(select)) \
            or not checkIsBone(active):
        return False
        #errorMsg = "Incorrect Selection: Active Object (last selected) must be a CTC Chain or Node and other selected object must be a Bone.\n"
        #errorMsg+= ("Selection is %d objects big, should be 1.\n"%len(selection) if len(selection)!=1 else "") +\
        #                ("%s is not a CTC Chain or Node.\n"%active.name if not(checkIsChain(active) or checkIsNode(active)) else "") +\
        #                ("%s is not a bone.\n"%selection[0].name if not(checkIsBone(selection[0])) else "")
        #raise ValueError(errorMsg)
    return True
      
class extendChain(bpy.types.Operator):        
    bl_idname = 'ctc_tools.extend_chain'
    bl_label = 'Extend Chain'
    bl_description = 'Insert Selected Bone after Selection on Chain'
    bl_options = {"REGISTER", "UNDO"}
    
    def validate(self,active,selection):
        chainRematchValidate(active, selection)
    
    def execute(self,context):
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        self.validate(active, selection)
        insert = createCTCNode(selection[0])
        formerContinuation = getDescendantOrNone(active)
        insert.parent = active
        if formerContinuation: formerContinuation.parent = insert
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}

class restartChain(bpy.types.Operator):
    bl_idname = 'ctc_tools.restart_chain'
    bl_label = 'Restart Chain'
    bl_description = 'Change Chain Start Bone Target and work downwards Recursively'
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        return chainRematchValidate(active, selection)
        
    def combineChain(self, chainEnd, skeletonEnd):
        ctcChain = getLowerChain(chainEnd)
        skeletonChain = []
        current = skeletonEnd
        for _ in range(len(ctcChain)):
            if not current:
                skeletonChain.append(None)
            else:
                if not checkIsBone(current):
                    raise ValueError("Non-bone on skeleton, or boneFunction missing in %s"%current.name)
                skeletonChain.append(current)
                current = getDescendantOrNone(current)
        for c,b in zip(ctcChain,skeletonChain):
            c.constraints["Bone Function"].target = b
        return
    
    def execute(self,context):
        select = bpy.context.active_object
        active = [obj for obj in bpy.context.selected_objects if obj != select][0]
        active = active.parent if checkIsStarFrame(active) else active
        #self.validate(active,selection)
        rootBone = select
        chainRoot = getChainEnd(active) if checkIsChain(active) else active
        self.combineChain(chainRoot, rootBone)
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}
    
class reendChain(bpy.types.Operator):
    bl_idname = 'ctc_tools.reend_chain'
    bl_label = 'Re-end Chain'
    bl_description = 'Change Chain End Bone Target and work upwards recurively'
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        return chainRematchValidate(active, selection)
        
    def getChainEnd(self, active):
        child = getChild(active)
        if not child:
            return active
        else:
            return self.getChainEnd(child)
    
    def combineChain(self, chainEnd, skeletonEnd):
        ctcChain = getUpperChain(chainEnd)
        skeletonChain = []
        current = skeletonEnd
        for _ in range(len(ctcChain)):
            if not current:
                raise ValueError("Skeleton start point is not deep enough to complete the chain.")
            if not checkIsBone(current):
                raise ValueError("Non-bone on skeleton, or boneFunction missing in %s"%current.name)
            skeletonChain.append(current)
            current = current.parent
        for c,b in zip(reversed(ctcChain),skeletonChain):
            c.constraints["Bone Function"].target = b
        return
    
    def execute(self,context):
        select = bpy.context.active_object
        active = [obj for obj in bpy.context.selected_objects if obj != select][0]
        active = active.parent if checkIsStarFrame(active) else active
        #self.validate(active,selection)
        rootBone = select
        chainRoot = self.getChainEnd(active) if checkIsChain(active) else active
        self.combineChain(chainRoot, rootBone)
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}
"""   
class changeNodeTarget(bpy.types.Operator):
    bl_idname = 'ctc_tools.change_target'
    bl_label = 'Change Bone Function'
    bl_description = 'Change CTC Node Bone Function Target'
    bl_options = {"REGISTER", "UNDO"}
    
    boneID = IntProperty(name = "New Bone Function ID",
                            description = "Assign New Bone Function to Active",
                            default = -1)
    def execute(self,context):
        active = bpy.context.active_object
        if not checkIsNode(active):
            raise ValueError("Active object is not a node.")
        try:
            rootco = findFunction(self.boneID)
        except:
            oldID = self.boneID
            self.boneID = 0
            if oldID != -1:
                rootco = None
            else:
                raise ValueError("Bone Function ID %d is not present in the skeleton."%oldID)
        active.constraints["Bone Function"].target = rootco
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}
"""

class realignChain(bpy.types.Operator):
    bl_idname = 'ctc_tools.realign_chain'
    bl_label = 'Realign Chain'
    bl_description = 'Realign Chain Visuals with Bones'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for bone in [b for b in bpy.context.scene.objects if checkIsChainStart(b)]:
            self.recursiveRealignNode(bone)
        bpy.context.scene.update()
        return {"FINISHED"}
    
    def recursiveRealignNode(self,node):
        parent = node.parent
        node.constraints["Bone Function"].inverse_matrix = parent.matrix_world.inverted()
        bpy.context.scene.update()
        for children in [n for n in node.children if checkIsNode(n)]:
            self.recursiveRealignNode(children)
        node.constraints["Bone Function"].target = node.constraints["Bone Function"].target
        bpy.context.scene.update()
    
class findDuplicates(bpy.types.Operator):
    bl_idname = 'ctc_tools.find_duplicates'
    bl_label = 'Find Duplicates'
    bl_description = 'Find Duplicate Bone Functions on Chain'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        functions = {}
        repeats = set()
        for node in [b for b in bpy.context.scene.objects if checkIsNode(b)]:
            bone = node.constraints["Bone Function"].target
            if bone:
                funcID = bone["boneFunction"]
            else:
                continue
            if funcID in functions:
                functions[funcID].append((node.name,bone.name))
                repeats.add(funcID)
            else:
                functions[funcID] = [(node.name,bone.name)]
        if repeats:
            ShowMessageBox("%d Repeated bone functions on CTC chains"%len(repeats), "Repeated Bone Functions", 'ERROR')
            print("%d Repeated Function IDs"%len(repeats))
            for r in repeats:
                print("\tFunction %d repeated %d times:"%(r,len(functions[r])))
                for n,b in functions[r]:
                    print("\t\t%s -> %s"%(n,b))            
        return {"FINISHED"}
    
class ctcAnon(bpy.types.Operator):
    bl_idname = 'mod_tools.clear_ctc_functions'
    bl_label = "Anonymize CTC Bones' Functions"
    bl_description = 'Sets free-physics bones to annoynimized functions.'
    bl_options = {"REGISTER", "PRESET", "UNDO"}   

    annon = StringProperty(
                        name = 'Anonymized ID',
                        description = 'Anonymized ID to use.',
                        default = "CTC_Annon_Function",
                        )

    def execute(self,context):
        for node in [o for o in bpy.context.scene.objects if o.type == "EMPTY" and checkIsNode(o)]:
            if "Bone Function" in node.constraints:
                target = node.constraints["Bone Function"].target
                if target and "boneFunction" in target:
                    target["boneFunction"] = self.annon
        return {'FINISHED'}
        #col.operator("mod_tools.clear_ctc_functions", icon='GROUP_BONE', text="Anonymize CTC Functions")

def testAnon(o):
    try:
        int(o["boneFunction"])
        return False
    except:                
        return True
       
class ctcDeanon(bpy.types.Operator):
    bl_idname = 'mod_tools.assign_ctc_functions'
    bl_label = "Deannonymize CTC Bones' Functions"
    bl_description = 'Assigns fixed ids to annonymized free-physics bones.'
    bl_options = {"REGISTER", "PRESET", "UNDO"}   

    annon = IntProperty(
                        name = 'Starting ID',
                        description = 'Starting ID to use.',
                        default = 0,
                        )
    only = BoolProperty(
                        name = 'Limit to Annonymized Functions',
                        description = 'Only rename annonymized functions.',
                        default = True,
                        )

    def execute(self,context):
        occupiedIDs = {o["boneFunction"] for o in bpy.context.scene.objects if o.type == "EMPTY" and "boneFunction" in o}
        i = self.annon
        for bone in [o for o in bpy.context.scene.objects if o.type == "EMPTY" and checkIsNode(o)]:
            if "Bone Function" in bone.constraints:
                target = bone.constraints["Bone Function"].target
                if target and "boneFunction" in target:
                    if not self.only or testAnon(target):
                        while i in occupiedIDs:
                            i+=1
                        target["boneFunction"] = i
                        i+=1
        return {'FINISHED'}         
                
        #col.operator("mod_tools.assign_ctc_functions", icon='GROUP_BONE', text="Deanonymize CTC Functions")
        
class ctcClear(bpy.types.Operator):
    bl_idname = 'mod_tools.delete_orphans'
    bl_label = "Delete Orphan CTC Functions"
    bl_description = 'Deletes bone with annonymized bone functions.'
    bl_options = {"REGISTER", "PRESET", "UNDO"}   

    def execute(self,context):
        objs = bpy.data.objects
        for bone in [o for o in bpy.context.scene.objects if o.type == "EMPTY" and "boneFunction" in o]:
            if testAnon(bone):
                for c in bone.children:
                    c.parent = bone.parent
                objs.remove(objs[bone.name], do_unlink=True)
        return {'FINISHED'}
        #col.operator("mod_tools.delete_orphans", icon='GROUP_BONE', text="Delete Orphan CTC Functions")
        
class ctcOrphan(bpy.types.Operator):
    bl_idname = 'mod_tools.delete_fixed'
    bl_label = "Delete Fixed Bone Functions"
    bl_description = 'Deletes bone with non annonymized bone functions.'
    bl_options = {"REGISTER", "PRESET", "UNDO"}   

    def execute(self,context):
        objs = bpy.data.objects
        for bone in [o for o in bpy.context.scene.objects if o.type == "EMPTY" and "boneFunction" in o]:
            if not testAnon(bone):
                for c in bone.children:
                    matrix = c.matrix_world
                    c.parent = bone.parent
                    c.matrix_world = matrix
                objs.remove(objs[bone.name], do_unlink=True)
        return {'FINISHED'}
        #col.operator("mod_tools.delete_fixed", icon='GROUP_BONE', text="Delete Fixed Functions")
    
class hideCTC(bpy.types.Operator):
    bl_idname = 'ctc_tools.hide_ctc'
    bl_label = 'Hide CTC Structures'
    bl_description = 'Hides all structures related to CTCs'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for empty in [obj for obj in bpy.context.scene.objects 
                      if obj.type == "EMPTY" and checkIsSubCTC(obj)]:
            empty.hide = True
        return {"FINISHED"}

class showCTC(bpy.types.Operator):
    bl_idname = 'ctc_tools.show_ctc'
    bl_label = 'Show CTC Structures'
    bl_description = 'Show all structures related to CTCs'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for empty in [obj for obj in bpy.context.scene.objects 
                      if obj.type == "EMPTY" and checkIsSubCTC(obj)]:
            empty.hide = False
        return {"FINISHED"}
    
checkIsArmatureRoot = checkStarType("MOD3_SkeletonRoot")
def pollValidEmpty(self,obj):
    return checkIsArmatureRoot(obj)

class toJSon(bpy.types.Operator):
    bl_idname = 'ctc_tools.chain_to_json'
    bl_label = 'DevTool: Print chain to console as json.'
    bl_description = 'DevTool: Converts currently selected chain into a json.'
    bl_options = {"REGISTER", "UNDO"}
    
    name = StringProperty(
                        name = 'Chain Name',
                        description = 'Name for the Chain.',
                        default = "Chain.000",
                        )
    
    def jsonHeader(self,head):
        return {prop:head[prop] for prop in head.keys() if "{" not in prop}
        
    def parseNode(self,node):
        if not node:
            return []
        nodes = []
        frame = getStarFrame(node)
        validProperties = {prop:frame[prop] for prop in frame.keys() if "{" not in prop}
        nodes.append(validProperties)
        return nodes + self.parseNode(getChild(node))
    
    def getFunction(self,chain):
        start = getChild(chain)
        try:
            return start.constraints["Bone Function"].target.parent["boneFunction"]
        except Exception as e:
            #print(e)
            return -1        
    
    def execute(self,context):
        result = {}
        chain = bpy.context.active_object
        header = self.jsonHeader(chain.parent)
        cheader = self.jsonHeader(chain)
        nodes = self.parseNode(getChild(chain))
        functionParent = self.getFunction(chain)
        result = {"name":self.name,"parent":functionParent,"file_header":header,"chain_header":cheader,"nodes":nodes}
        print(str(result).replace("'",'"'))
        return {"FINISHED"}
    
    @classmethod
    def poll(cls,context):
        return bpy.context.active_object and checkIsChain(bpy.context.active_object)

def getChainFrames(chain):
    node = getChild(chain)
    results = []
    while node != None:
        frame = getStarFrame(node)
        results.append(frame)
        node = getChild(node)
    return results

class applyPreset(bpy.types.Operator):
    bl_idname = 'ctc_tools.apply_preset'
    bl_label = 'Apply ctc preset to chains.'
    bl_description = 'Applies preset to selected ctc chains.'
    bl_options = {"REGISTER", "UNDO"}

    preset = EnumProperty(
        name = "Preset Properties",
        description = "Load a preset for chain properties.",
        items = getPresets,
        )    

    @staticmethod
    def applyPreset(chain,preset):
        for key,val in preset.chain_definition.items():
            chain[key] = val
        selection = getChainFrames(chain)
        for bone,presetEntry in list(zip(selection[:-1],preset))+[(selection[-1],preset.endNode())]:
            for key,val in presetEntry.items():
                bone[key] = val
    
    @staticmethod
    def applyHeader(header,preset):
        for key,val in preset.file_header.items():
            header[key] = val
    
    def execute(self,context):
        selection = [entry for entry in bpy.context.scene.objects if entry.select]
        for entry in selection:
            if checkIsChain(entry):
                self.applyPreset(entry,findPreset(self.preset))
            if checkIsCTC(entry):
                self.applyHeader(entry,findPreset(self.preset))
        return {"FINISHED"}

    #@classmethod
    #def poll(cls,ctx):
    #    return False    

    #@classmethod
    #def poll(cls,context):
    #    return bpy.context.active_object and checkIsChain(bpy.context.active_object)

def createEmpty(name,position):
    o = bpy.data.objects.new( name, None )
    bpy.context.scene.objects.link( o )
    #print(position)
    o.location = position
    #print(o.location)
    return o    

def validEmpties(ctx,obj):
    return [(empty.name,empty.name,"Empty Armature") for empty in bpy.context.scene.objects if pollValidEmpty(ctx,empty)]
        

class convertArmature(bpy.types.Operator):
    bl_idname = 'ctc_tools.armature_to_ctc'
    bl_label = 'Convert Blender Armature and Meshes to CTC'
    bl_description = 'Converts Blender Armatures and Meshes to CTC Nodes and appends them to an Empty Hierarchy'
    bl_options = {"REGISTER", "UNDO"}
    
    emptyArmature = EnumProperty(
        name = "Empty Armature",
        description = "Armature to which the hair ctc strands will be appended to.",
        items = validEmpties,
        )
    preset = EnumProperty(
        name = "Preset Properties",
        description = "Load a preset for chain properties.",
        items = getPresets,
        )
    startIndex = IntProperty(name = "Starting Bone Function.",
        description = "Set index from which bone's Bone Function will start being autogenerated.",
        default = 150)
    convertAll = BoolProperty(
        name = "Convert All",
        description = "Convert all armatures in the scene",
        default = False)
    
    #@classmethod
    #def poll(cls,ctx):
    #    return False
    
    def invalidFunctions(self,armatureRoot):
        listing = []
        if "boneFunction" in armatureRoot:
            listing.append(armatureRoot["boneFunction"])
        for child in armatureRoot.children:
            listing += self.invalidFunctions(child)
        return listing
      
                
    def strandsFromTips(self,chain):
        strands = []
        for tip in [bone for bone in chain.data.edit_bones if not bone.children]:
            strand = [tip]
            current = tip.parent
            while (current):
                strand.append(current)
                current = current.parent
            strands.append(list(reversed(strand)))
        return strands
    
    def getChainPositions(self,chain):
        strands = []
        MTF = Matrix([[0,1,0,0],[1,0,0,0],[0,0,-1,0],[0,0,0,-1]])
        for catena in self.strandsFromTips(chain):
            positions = []
            transforms = []
            names = []
            for bone in catena:
                positions.append(chain.matrix_world*bone.head)
                transforms.append(chain.matrix_world*bone.matrix*MTF)
                names.append(bone.name)
            positions.append(chain.matrix_world*bone.tail)
            m = Matrix.Identity(4)
            tailPosition = chain.matrix_world*bone.tail
            for i in range(3): m[i][3] = tailPosition[i]
            transforms.append(m)
            names.append(bone.name)#Set format for the "loose" bone
            strands.append((positions,transforms,names))
        return strands
    
    #unkn2 = 0
    def emptyChain(self,positions,startIndex,validator,names):
        current = startIndex
        parent = None
        nodes = []
        namesOut = {}
        for pos,name in zip(positions,names):
            empty = createEmpty("CTC_Bone",pos)
            while not validator(current):
                current+=1
            empty["boneFunction"] = current
            empty["unkn2"] = 0
            #weakReparent(empty,parent)
            empty.parent = parent
            parent = empty
            nodes.append(empty)
            namesOut[name] = empty.name
        bpy.context.scene.update()
        prevLoc = Vector((0,0,0))
        for pos,node in zip(positions,nodes):
            node.location = pos-prevLoc
            prevLoc = pos
        return nodes, current, namesOut
    
    def createNodes(self,selection,chainStart,preset,orientations):
        chain = []
        parent = chainStart 
        for bone,presetEntry in list(zip(selection[:-1],preset))+[(selection[-1],preset.endNode())]:
            #if first:
            #    first = False
            #    bprop["fixedEnd"]=True
            node = createCTCNode(bone,1,Matrix.Identity(4),*presetEntry.items())
            node.parent = parent
            bpy.context.scene.update()
            node.constraints["Bone Function"].inverse_matrix = parent.matrix_world.inverted()
            parent = node
            chain.append(node)
        #bpy.context.scene.update()
        for node,trn in zip(chain,orientations):
            for i in range(3): trn[i][3] = 0
            getStarFrame(node).matrix_world = trn
            getStarFrame(node).location = (0,0,0)
            #print(trn)
        #for (parent,nextParent),(node,nextNode) in zip(zip(bpy.selection,bpy.selection[1:]),zip(chain,chain[1:])):                                                         
        #    orientToActive.orientVectorSystem(node,nextParent,Vector([1,0,0]),parent)
    
    def renameMeshes(self,chain,remaps):
        for child in chain.children:
            if child.type == "MESH":
                for g in child.vertex_groups:
                    if g.name in remaps:
                        g.name = remaps[g.name]
    
    def convertChain(self,chain,startIndex,invalidValues,preset):
        invalidValues = set(invalidValues)
        validator = lambda x: x not in invalidValues
        bpy.context.scene.objects.active = chain
        bpy.ops.object.mode_set(mode="EDIT")
        strands = self.getChainPositions(chain)
        bpy.ops.object.mode_set(mode="OBJECT")
        for positions,transforms,names in strands:
            emptyNodes,newStart,nameMapping = self.emptyChain(positions,startIndex,validator,names)
            self.renameMeshes(chain,nameMapping)
            chainStart = createChain(*preset.chain_definition.items())
            self.createNodes(emptyNodes,chainStart,preset,transforms)
        return emptyNodes[0],newStart
        
    def growArmature(self,base,extensions,func):
        rootbone = self.fetchRoot(base,func)
        if not rootbone: 
            rootbone = base
        for root in extensions:
            mw = copy.deepcopy(root.matrix_world)
            root.parent = rootbone
            root.matrix_world = mw
    #self.preset.rootID()
    def fetchRoot(self,base,rootID):
        if "boneFunction" in base and base["boneFunction"] == rootID:
            return base
        for child in base.children:
            candidate = self.fetchRoot(child,rootID)
            if candidate:
                return candidate
        return None        
    
    def findArmature(self,emptyArmatureName):
        for e in bpy.context.scene.objects:
            if emptyArmatureName == e.name:
                return e
        return None
    
    def fetchChains(self):
        if self.convertAll:
            return [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
        else:
            return [mesh for mesh in bpy.context.scene.objects if mesh.type == "ARMATURE" and mesh.select]
    
    def execute(self,context): 
        armature = self.findArmature(self.emptyArmature)
        startPoint = self.startIndex
        invalidValues = self.invalidFunctions(armature)
        hairRoots = []
        for chain in self.fetchChains():
            root,startPoint = self.convertChain(chain,startPoint,invalidValues,findPreset(self.preset))
            hairRoots.append(root)
        self.growArmature(armature,hairRoots,findPreset(self.preset).rootID())
        return {"FINISHED"}