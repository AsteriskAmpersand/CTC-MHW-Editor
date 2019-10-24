# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 14:09:29 2019

@author: AsteriskAmpersand
"""
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from mathutils import Vector, Matrix
from ..structures.Ccl import CclFile
import bmesh

class ImportCCL(Operator, ImportHelper):
    bl_idname = "custom_import.import_mhw_ccl"
    bl_label = "Load MHW CCL file (.ccl)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".ccl"
    filter_glob = StringProperty(default="*.ccl", options={'HIDDEN'}, maxlen=255)
    
    createmesh = BoolProperty(
        name = "Add the collision capsule as a mesh",
        description = "Renders the collision capsule's mesh on import.",
        default = False)
    
    """
    clear_scene = BoolProperty(
        name = "Clear scene before import.",
        description = "Clears all contents before importing",
        default = True)
    maximize_clipping = BoolProperty(
        name = "Maximizes clipping distance.",
        description = "Maximizes clipping distance to be able to see all of the model at once.",
        default = True)"""

    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        ccl = CclFile(self.properties.filepath)
        for ix, entry in enumerate(ccl.data):
            try:
                capsule = self.createCapsule(entry)
                capsule.name = "%d Capsule"%ix
            except Exception as e: 
                print(e)                
        return {'FINISHED'}
    
    @staticmethod
    def findFunction(functionID):
        match = [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY" 
                 and "boneFunction" in obj and obj["boneFunction"] == functionID]
        if len(match) != 1:
            raise ValueError(("Multiple" if len(match) else "No" )+" Function ID Matches for %d"%functionID)
        return match[0]

    @staticmethod
    def transToMat(coordinates):
        m = Matrix.Identity(4)
        m[0][3], m[1][3], m[2][3] = coordinates[0:3]
        return m
    
    @staticmethod
    def insertRadiusToMat(radius,matrix):
        matrix[0][:3] = Vector(matrix[0][:3])*radius
        matrix[1][:3] = Vector(matrix[1][:3])*radius
        matrix[2][:3] = Vector(matrix[2][:3])*radius
        return matrix
    
    @staticmethod
    def joinEmpties(obs):
        o = bpy.data.objects.new("Capsule", None )
        bpy.context.scene.objects.link( o )
        for ob in obs:
            ob.parent = o
        return o
        """
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
        """
        
    @staticmethod
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
        

    def createGeometry(self, offset, radius, function):
        rootco = self.findFunction(function)#.matrix_world.translation
        #Empty
        offset = self.insertRadiusToMat(radius,self.transToMat(offset))
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
    
    def createMesh(self, offset, radius, function):
        rootco = self.findFunction(function).matrix_world.translation
        finalco = rootco+offset
        finalcoMatrix = self.transToMat(finalco)
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
    
    def deleteObject(self, ob):
        objs = bpy.data.objects
        objs.remove(objs[ob.name], do_unlink=True)
        return
    
    def convexHull(self,ob):
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
        self.deleteObject(ob)
        return copy
    
    def createCapsule(self, record):
        r1,co1 = record.startsphere_radius, Vector([record.startsphere_xOffset, 
                                                    record.startsphere_yOffset, 
                                                    record.startsphere_zOffset])
        r2,co2 = record.endsphere_radius, Vector([record.endsphere_xOffset,
                                                  record.endsphere_yOffset, 
                                                  record.endsphere_zOffset])
        s1 = self.createGeometry(co1, r1, record.boneIDOne)
        s1.name = "Start Sphere"
        s1["Type"] = "CCL_SPHERE"
        s1["Position"] = "Start"
        s2 = self.createGeometry(co2, r2, record.boneIDTwo)
        s2.name = "End Sphere"
        s2["Type"] = "CCL_SPHERE"
        s2["Position"] = "End"
        s = self.joinEmpties([s1,s2])
        #hull = self.convexHull(s)
        s.name = "Collision Capsule"
        s["Type"] = "CCL"
        s["Data"] = record.unknownFrontBytesCont + record.unknownEndBytes
        if self.createmesh:
            m1 = self.createMesh(co1, r1, record.boneIDOne)
            m2 = self.createMesh(co2, r2, record.boneIDTwo)
            m = self.joinObjects([m1,m2])
            hull = self.convexHull(m)
            hull.name = "Collision Capsule Mesh"
            hull.parent = s
        return s
    
    
def menu_func_import(self, context):
    self.layout.operator(ImportCCL.bl_idname, text="MHW CCL (.ccl)")
