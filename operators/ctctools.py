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
from bpy.props import IntProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty
from ..operators.ccltools import findFunction

def createCTCHeader(ucis,uci,ticks,pose,damp,react,grav,windM,windL,windH,ufs):
    header = bpy.data.objects.new("CtcHeader", None )
    bpy.context.scene.objects.link( header )
    #mod.inverse_matrix = node.matrix #experiment into the meaning of the matrix
    header.empty_draw_size = 0
    header.empty_draw_type = "SPHERE"
    header.show_x_ray = True
    for i,ucv in enumerate(ucis): header["unknownsConstantIntSet%d"%i] = ucv 
    header["unknownConstantInt"] = uci
    header["updateTicks"] = ticks
    header["poseSnapping"] = pose
    header["chainDamping"] = damp
    header["reactionSpeed"] = react
    header["gravityMult"] = grav
    header["windMultMid"] = windM
    header["windMultLow"] = windL
    header["windMultHigh"] = windH
    for i,uf in enumerate(ufs): header["unknownFloatSet%d"%i] = uf
    header["Type"] = "CTC"
    return header

def createChain(col,w,ub,xg,yg,zg,xi,yi,zi,uf1,uf2,uf3,wm,lod):
    chain = bpy.data.objects.new("CtcChain", None )
    bpy.context.scene.objects.link( chain )
    chain["Type"] = "CTC_Chain"
    chain.empty_draw_size = .75
    chain.empty_draw_type = "CIRCLE"
    chain.show_x_ray = True
    chain["collision"] = col
    chain["weightiness"] = w
    for i,byte in enumerate(ub): chain["unknownBytes%02d"%i] = byte
    chain["xGravity"] = xg
    chain["yGravity"] = yg
    chain["zGravity"] = zg
    chain["xInertia"] = xi
    chain["yInertia"] = yi
    chain["zInertia"] = zi
    chain["unknownFloatTwo"] = uf1
    chain["unknownFloatThree"] = uf2
    chain["unknownFloatFour"] = uf3
    chain["windMultiplier"] = wm
    chain["lod"] = lod
    return chain

def createCTCNode(rootco,ubst = [0]*5,vec = Vector([0,0,0]),mat = Matrix.Identity(4)):
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
            o["UnknownByte%02d"%i] = ubst[i]
        o["Vector"] = vec
        o["Matrix"] = mat
        return o

def checkIsStarType(candidateStarType):
    return candidateStarType.type == "EMPTY" and "Type" in candidateStarType
    
def checkStarType(typing):
    return lambda x: checkIsStarType(x) and x["Type"]==typing

def getChild(candidate):
    generator = (c for c in candidate.children if checkStarType("CTC_Node")(c))
    try: w = next(generator)
    except: return None
    try: next(generator)
    except: return w
    raise ValueError("Forked chain not under specification %s"%candidate.name)

checkIsCTC = checkStarType("CTC")
checkIsChain = lambda x: checkStarType("CTC_Chain")(x) and (getChild(x) or True)
checkIsNode = lambda x: checkStarType("CTC_Node")(x) and (getChild(x) or True)
checkIsChainStart = lambda x:checkIsNode(x) and x.parent and checkIsChain(x.parent)
checkIsChainEnd = lambda x:checkIsNode(x) and len([w for w in x.children if checkIsNode(w)]) == 0
checkIsBone = lambda x: x.type == "EMPTY" and "boneFunction" in x

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
                       keyword = lambda x: abs(int(x["boneFunction"])-bone["boneFunction"]))
    if children:
        return children[0]
    else: return None
    
def getChainEnd(active):
    child = getChild(active)
    if not child:
        if checkIsChain(active):
            raise ValueError("Chain has no nodes")
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
    
    ucis = EnumProperty(
            name = "Unknown Int Set",
            description = "Set of 4 Unknown Ints",
            items = [
                    ('(27, 143, 140)', "(27, 143, 140)", ""),
                    ('(27, 0, 1000)', "(27, 0, 100)", ""),
                    ]
            )
    uci = EnumProperty(
            name = "Unknown Int",
            description = "Unknown Int with Flag Structure",
            items = [
                    ('0', "00000000 00000000 00000000 00000000", ""),
                    ('64', "00000000 00000000 00000000 01000000", ""),
                    ('4160', "00000000 00000000 00000000 00000000", ""),
                    ('8256', "00000000 00000000 00000000 01000000", ""),
                    ('268435456', "00010000 00000000 00000000 00000000", ""),
                    ])
    ticks = FloatProperty(
            name = "Update Frequency",
            description = "Number of seconds between updates.",
            default = 1/6
            )
    pose = FloatProperty(
            name = "Pose Restitution Factor",
            description = "Plasticity in returning to the original position.",
            default = 1.0
            )
    damp = FloatProperty(
            name = "Dampening",
            description = "Dampening coefficient.",
            default = 1.0
            )
    react = FloatProperty(
            name = "Reaction Speed",
            description = "Sensitivity to Movement.",
            default = 1.0
            )
    grav = FloatProperty(
            name = "Gravity Multiplier",
            description = "Global multiplier to gravity values.",
            default = 1.0
            )
    windL = FloatProperty(
            name = "Low Wind Multiplier",
            description = "Global multiplier to Weak Wind values.",
            default = 1.0
            )
    windM = FloatProperty(
            name = "Medium Wind Multiplier",
            description = "Global multiplier to Medium Wind values.",
            default = 1.0
            )
    windH = FloatProperty(
            name = "High Wind Multiplier",
            description = "Global multiplier to Strong Wind values.",
            default = 1.0
            )
    uf1 = FloatProperty(
            name = "Unknown Float 1",
            description = "Unknown Float Value.",
            default = 0.2
            )
    uf2 = FloatProperty(
            name = "Unknown Float 2",
            description = "Unknown Float Value.",
            default = 0.3
            )    
    uf3 = FloatProperty(
            name = "Unknown Float 3",
            description = "Unknown Float Value.",
            default = 0.2
            )    
    
    def execute(self,context):
        ufs = self.uf1, self.uf2, self.uf3
        createCTCHeader(
                eval(self.ucis),
                eval(self.uci),
                self.ticks,
                self.pose,
                self.damp,
                self.react,
                self.grav,
                self.windM,
                self.windL,
                self.windH,
                ufs)
        return {"FINISHED"}
    
class chainFromSelection(bpy.types.Operator):        
    bl_idname = 'ctc_tools.chain_from_selection'
    bl_label = 'Create CTC Chain'
    bl_description = 'Create CTC Chain from Selection'
    bl_options = {"REGISTER", "UNDO"}

    col = IntProperty(
            name = "Collision Type",
            description = "Collision Type Enumeration Index.",
            default = 4
            )
    w = IntProperty(
            name = "Weightiness",
            description = "Weight Dynamics Type Enumeration Index.",
            default = 7
            )
    xg = FloatProperty(
            name = "X-Axis Gravity",
            description = "Gravity Force along X Axis.",
            default = 0.0
            )
    yg = FloatProperty(
            name = "Y-Axis Gravity",
            description = "Gravity Force along Y Axis.",
            default = 980.0
            )
    zg = FloatProperty(
            name = "Z-Axis Gravity",
            description = "Gravity Force along Z Axis.",
            default = 0.0
            )
    xi = FloatProperty(
            name = "Pose Snapping",
            description = "Restitution Force to Original Position.",
            default = 0.05
            )
    yi = FloatProperty(
            name = "Cone of Motion",
            description = "Suspected Steradian Limitation to Motion.",
            default = 0.8
            )
    zi = FloatProperty(
            name = "Tension",
            description = "Restitution Speed to Original Position",
            default = 0.005
            )
    uf1 = FloatProperty(
            name = "Unknown Float 1",
            description = "Unknown",
            default = 100.0
            )
    uf2 = FloatProperty(
            name = "Unknown Float 2",
            description = "Unknown",
            default = 0.0
            )
    uf3 = FloatProperty(
            name = "Unknown Float 3",
            description = "Unknown",
            default = .1
            )
    wm = FloatProperty(
            name = "Wind Multiplier",
            description = "Strength of wind on Chain",
            default = 0.7
            )
    lod = IntProperty(
            name = "Level of Detail",
            description = "Level of Detail index on which the physics are calculated.",
            default = 65535
            )
    
    def buildChain(self,selection, chainStart):
        parent = chainStart
        for bone in bpy.selection:
            node = createCTCNode(bone,[0]*5,Vector([0,0,0,1]),Matrix.Identity(4))
            node.parent = parent
            bpy.context.scene.update()
            node.constraints["Bone Function"].inverse_matrix = parent.matrix_world.inverted()
            parent = node
    
    def validate(self,selection):
        for bone in selection:
            if not checkIsBone(bone):
                raise ValueError("Non-bone on selection: %s"%bone.name)
    
    def execute(self,context):
        selection = bpy.selection
        self.validate(selection)
        chainStart = createChain(self.col,self.w,
                                 [0]*14,#2+12
                                 self.xg,self.yg,self.zg,
                                 self.xi,self.yi,self.zi,
                                 self.uf1,self.uf2,self.uf3,
                                 self.wm,self.lod)
        self.buildChain(selection,chainStart)
        return {"FINISHED"}
    
def chainRematchValidate(active,selection):
    if len(selection)!=1 or not(checkIsChain(active) or checkIsNode(active)) or not checkIsBone(selection[0]):
            errorMsg = "Incorrect Selection: Active Object (last selected) must be a CTC Chain or Node and other selected object must be a Bone.\n"
            errorMsg+= ("Selection is %d objects big, should be 1.\n"%len(selection) if len(selection)!=1 else "") +\
                            ("%s is not a CTC Chain or Node.\n"%active.name if not(checkIsChain(active) or checkIsNode(active)) else "") +\
                            ("%s is not a bone.\n"%selection[0].name if not(checkIsBone(selection[0])) else "")
            raise ValueError(errorMsg)
      
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
        insert = createCTCNode(active)
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
    
    def validate(self, active, selection):
        chainRematchValidate(active, selection)
        
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
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        self.validate(active,selection)
        rootBone = selection[0]
        chainRoot = getChainEnd(active) if checkIsChain(active) else active
        self.combineChain(chainRoot, rootBone)
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}
    
class reendChain(bpy.types.Operator):
    bl_idname = 'ctc_tools.reend_chain'
    bl_label = 'Re-end Chain'
    bl_description = 'Change Chain End Bone Target and work upwards recurively'
    bl_options = {"REGISTER", "UNDO"}
    
    def validate(self, active, selection):
        chainRematchValidate(active, selection)
        
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
            current = skeletonEnd.parent
        for c,b in zip(reversed(ctcChain),skeletonChain):
            c.constraints["Bone Function"].target = b
        return
    
    def execute(self,context):
        active = bpy.context.active_object
        selection = [obj for obj in bpy.context.selected_objects if obj != active]
        self.validate(active,selection)
        rootBone = selection[0]
        chainRoot = self.getChainEnd(active) if checkIsChain(active) else active
        self.combineChain(chainRoot, rootBone)
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}
    
class changeNodeTarget(bpy.types.Operator):
    bl_idname = 'ctc_tools.change_target'
    bl_label = 'Change Bone Function'
    bl_description = 'Change CTC Node Bone Function Target'
    bl_options = {"REGISTER", "UNDO"}
    
    boneID = IntProperty(name = "New Bone Function ID",
                            description = "Assign New Bone Function to Active",
                            default = False)
    def execute(self,context):
        active = bpy.context.active_object
        if not checkIsNode(active):
            raise ValueError("Active object is not a node.")
        try:
            rootco = findFunction(self.boneID)
        except:
            oldID = self.boneID
            self.boneID = 0
            if oldID != 0:
                rootco = None
            else:
                raise ValueError("Bone Function ID %d is not present in the skeleton."%self.oldID)
        active.constraints["Bone Function"].target = rootco
        bpy.ops.ctc_tools.realign_chain()
        return {"FINISHED"}

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
    