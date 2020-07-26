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
from ..operators.ccltools import findFunction,checkSubStarType,checkStarType,checkIsStarType
from ..structures.Ctc import ARecord,BRecord,Header
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

def createCTCHeader(*args):
    header = bpy.data.objects.new("CtcHeader", None )
    bpy.context.scene.objects.link( header )
    #mod.inverse_matrix = node.matrix #experiment into the meaning of the matrix
    header.empty_draw_size = 0
    header.empty_draw_type = "SPHERE"
    header.show_x_ray = True
    for name,prop in args:
        writeProp(header,name,prop)
    #for i,ucv in enumerate(ucis): header["unknownsConstantIntSet%d"%i] = ucv 
    #header["unknownConstantInt"] = uci
    #header["updateTicks"] = ticks
    #header["poseSnapping"] = pose
    #header["chainDamping"] = damp
    #header["reactionSpeed"] = react
    #header["gravityMult"] = grav
    #header["windMultMid"] = windM
    #header["windMultLow"] = windL
    #header["windMultHigh"] = windH
    #for i,uf in enumerate(ufs): header["unknownFloatSet%d"%i] = uf
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
        print(name)
        print(prop)
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
            default = 39
            )
    lod = IntProperty(
            name = "Level of Detail",
            description = "Level of Detail index on which the physics are calculated",
            default = -1
            )
    ubs = EnumProperty(
            name = "Unknown Byte Pair",
            description = "Unknown Pair of data as Bytes",
            items = [(str(tuppling),str(tuppling),"") for tuppling in 
                     [(1, 2), (0, 1), (0, 0), (32, 0), (96, 0), (64, 0), (17, 0), (17, 1), (17, 2), (16, 0), (1, 1), (80, 0), (1, 0), (0, 2), (68, 0), (4, 0)]
                    ],
            default = "(0, 0)"
            )
    xg = FloatProperty(
            name = "X-Axis Gravity",
            description = "Gravity Force along X Axis.",
            default = 0.0
            )
    yg = FloatProperty(
            name = "Y-Axis Gravity",
            description = "Gravity Force along Y Axis.",
            default = -980.0
            )
    zg = FloatProperty(
            name = "Z-Axis Gravity",
            description = "Gravity Force along Z Axis.",
            default = 0.0
            )
    xi = FloatProperty(
            name = "Pose Snapping",
            description = "Restitution Force to Original Position.",
            default = 0.5
            )
    yi = FloatProperty(
            name = "Cone of Motion",
            description = "Suspected Steradian Limitation to Motion.",
            default = 0.5
            )
    zi = FloatProperty(
            name = "Tension",
            description = "Restitution Speed to Original Position",
            default = 0.5
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
            default = 1.0
            )
    
    def buildChain(self,selection, chainStart):
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
        for (parent,nextParent),(node,nextNode) in zip(zip(bpy.selection,bpy.selection[1:]),
                                                         zip(chain,chain[1:])):
            orientToActive.orientVectorSystem(node,nextParent,Vector([1,0,0]),parent)
    
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
        arecord = ARecord.defaultProperties.copy()
        arecord["collision"] = self.col
        arecord["weightiness"] = self.w
        arecord["unknownByteSet"] = eval(self.ubs)
        arecord["xGravity"] = self.xg
        arecord["yGravity"] = self.yg
        arecord["zGravity"] = self.zg
        arecord["unknownFloatTwo"] = self.uf1
        arecord["unknownFloatThree"] = self.uf2
        arecord["unknownFloatFour"] = self.uf3
        arecord["windMultiplier"] = self.wm
        arecord["lod"] = self.lod
        chainStart = createChain(*rename(arecord.items(),ARecord))
        self.buildChain(selection,chainStart)
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