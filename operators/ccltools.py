# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 02:06:30 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator
from mathutils import Vector, Matrix
from ..structures.Ccl import CclFile
import bmesh


def getCol(matrix, column):
    return [matrix[i][column] for i in range(len(matrix))]

def findFunction(functionID):
    match = [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY" 
             and "boneFunction" in obj and obj["boneFunction"] == functionID]
    if len(match) != 1:
        raise ValueError(("Multiple" if len(match) else "No" )+" Function ID Matches for %d"%functionID)
    return match[0]

def transToMat(coordinates):
    m = Matrix.Identity(4)
    m[0][3], m[1][3], m[2][3] = coordinates[0:3]
    return m

def insertRadiusToMat(radius,matrix):
    matrix[0][:3] = Vector(matrix[0][:3])*radius
    matrix[1][:3] = Vector(matrix[1][:3])*radius
    matrix[2][:3] = Vector(matrix[2][:3])*radius
    return matrix

def convexHull(ob):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    copy = ob.copy()
    ch = bpy.data.meshes.new("%s convexhull" % me.name)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.to_mesh(ch)
    copy.data = ch
    bpy.context.scene.objects.link(copy)
    bm.free()
    deleteObject(ob)
    return copy

def createMesh(offset, radius, bone):
    rootco = bone.matrix_world.translation
    finalco = rootco+offset
    finalcoMatrix = transToMat(finalco)
    bpyscene = bpy.context.scene        
    # Create an empty mesh and the object.
    mesh = bpy.data.meshes.new('CapsuleSphere')
    basic_sphere = bpy.data.objects.new("CapsuleSphere", mesh)        
    # Add the object into the scene.
    bpyscene.objects.link(basic_sphere)
    bpyscene.objects.active = basic_sphere
    basic_sphere.select = True        
    # Construct the bmesh sphere and assign it to the blender mesh.
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, diameter=radius, 
                              u_segments=32, v_segments=16,
                              matrix = finalcoMatrix)
    bm.to_mesh(mesh)
    bm.free()
    return basic_sphere

def deleteObject(ob):
    objs = bpy.data.objects
    objs.remove(objs[ob.name], do_unlink=True)
    return

def cleanCapsule(capsule):
    for mesh in [mesh for mesh in capsule.children if mesh.type == "MESH"]:
        deleteObject(mesh)
        
def capsuleData(capsule):
    co, r, i = [], [], []
    for node in [empty for empty in capsule.children if empty.type == "EMPTY"]:
        co.append(Vector(getCol(node.matrix_basis,3)[0:3]))
        r.append(node.matrix_basis[0][0])
        i.append(node.constraints["Bone Function"].target)
    return co[0],r[0],i[0],co[1],r[1],i[1]

def joinObjects(obs):
    scene = bpy.context.scene
    ctx = bpy.context.copy()
    if not obs:
        return
    # one of the objects to join
    ctx['active_object'] = obs[0]        
    ctx['selected_objects'] = obs        
    # we need the scene bases as well for joining
    ctx['selected_editable_bases'] = [scene.object_bases[ob.name] for ob in obs]        
    bpy.ops.object.join(ctx)
    return obs[0]

def renderCapsules(capsule):
    co1, r1, boneOne, co2, r2, boneTwo = capsuleData(capsule)
    m1 = createMesh(co1, r1, boneOne)
    m2 = createMesh(co2, r2, boneTwo)
    m = joinObjects([m1,m2])
    hull = convexHull(m)
    hull.name = "Collision Capsule Mesh"
    hull.parent = capsule
        
def createGeometry(offset, radius, rootco):
    offset = insertRadiusToMat(radius,transToMat(offset))
    o = bpy.data.objects.new("Capsule", None )
    bpy.context.scene.objects.link( o )
    mod = o.constraints.new(type = "CHILD_OF")#name= "Bone Function"
    mod.name = "Bone Function"
    mod.target = rootco
    o.matrix_basis = offset
    result = o
    o.show_bounds = True
    o.draw_bounds_type = "SPHERE"
    return result

def joinEmpties(obs):
    o = bpy.data.objects.new("Capsule", None )
    bpy.context.scene.objects.link( o )
    for ob in obs:
        ob.parent = o
    return o
        
def createCapsule(f1,f2,r1,r2,co1=Vector([0,0,0]),co2=Vector([0,0,0])):
    s1 = createGeometry(co1, r1, f1)
    s1.name = "Start Sphere"
    s1["Type"] = "CCL_SPHERE"
    s1["Position"] = "Start"
    s2 = createGeometry(co2, r2, f2)
    s2.name = "End Sphere"
    s2["Type"] = "CCL_SPHERE"
    s2["Position"] = "End"
    s = joinEmpties([s1,s2])
    #hull = self.convexHull(s)
    s.name = "Collision Capsule"
    s["Type"] = "CCL"
    s["Data"] = [0]*8+[0]*4
    return s

class CCLTools(bpy.types.Panel):
    bl_idname = "panel.mhw_physics"
    bl_label = "CCL Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    # bl_category = "Tools"
    bl_category = "MHW Physics"

    def draw(self, context):
        self.layout.label("CCL Capsule Tools")
        self.layout.operator("ccl_tools.mesh_from_capsule", icon='MESH_CUBE', text="Mesh from Capsule")
        self.layout.operator("ccl_tools.capsule_from_selection", text="Capsule from Selection")
        self.layout.label("CCL Data Tools")
        self.layout.operator('ccl_tools.copy_data', text="Copy Unknowns")
        self.layout.operator('ccl_tools.paste_data', text="Paste Unknowns")

class CapsuleFromSelection(bpy.types.Operator):
    bl_idname = 'ccl_tools.capsule_from_selection'
    bl_label = 'CCL Capsule From Selection'
    bl_options = {"REGISTER", "UNDO"}
    r1 = FloatProperty(
        name = "Start Sphere Radius" ,
        description = "Starting Sphere Radius (Tends to be 0 Radius)",
        default = 0.0)
    r2 = FloatProperty(
        name = "End Sphere Radius" ,
        description = "End Sphere",
        default = 1.0)
    def execute(self,context):
        endco =  bpy.context.scene.objects.active
        selection = next((obj for obj in bpy.context.selected_objects if obj != endco))
        if "boneFunction" not in endco or "boneFunction" not in selection:
            raise ValueError("Selected Bone missing a Bone Function")
        createCapsule(selection,endco,self.r1,self.r2)
        return {"FINISHED"}

class MeshFromCapsule(bpy.types.Operator):
    bl_idname = 'ccl_tools.mesh_from_capsule'
    bl_label = 'Render CCL Capsule'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        capsule = bpy.context.scene.objects.active
        if capsule.type != "EMPTY" or "Type" not in capsule or capsule["Type"] != "CCL":
            raise ValueError("Not a ccl capsule")
        cleanCapsule(capsule)
        subcapsules = [child for child in capsule.children if "Type" in child and child["Type"] == "CCL_SPHERE"]
        if len(subcapsules) != 2:
            raise ValueError ("Corrupted capsule doesn't have exactly 2 empty CCL_SPHERE")
        renderCapsules(capsule)
        return {"FINISHED"}
    
copyBuffer = None
class CopyCCLData(bpy.types.Operator):    
    bl_idname = 'ccl_tools.copy_data'
    bl_label = 'Copy Capsule Unknown Data'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        capsule = bpy.context.scene.objects.active
        if capsule.type != "EMPTY" or "Type" not in capsule or capsule["Type"] != "CCL" or "Data" not in capsule:
            raise ValueError("Not a ccl capsule")
        global copyBuffer
        copyBuffer = list(capsule["Data"]).copy()
        return {"FINISHED"}
    
class PasteCCLData(bpy.types.Operator):    
    bl_idname = 'ccl_tools.paste_data'
    bl_label = 'Paste Capsule Unknown Data'
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        capsule = bpy.context.scene.objects.active
        if capsule.type != "EMPTY" or "Type" not in capsule or capsule["Type"] != "CCL":
            raise ValueError("Not a ccl capsule")
        global copyBuffer
        if copyBuffer == None:
            raise ValueError("Nothing on copy buffer")
        capsule["Data"] = list(copyBuffer).copy()
        return {"FINISHED"}