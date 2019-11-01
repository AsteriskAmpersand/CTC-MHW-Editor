# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 13:38:47 2019

@author: AsteriskAmpersand
"""
#from .dbg import dbg_init
#dbg_init()

content=bytes("","UTF-8")
bl_info = {
    "name": "MHW CTC & CCL Importer",
    "category": "Import-Export",
    "author": "AsteriskAmpersand (Code), UberGrainy, Statyk & Karbon (Structure)",
    "location": "File > Import-Export > Mod3/MHW",
    "version": (1,0,0)
}
 
import bpy

from .operators.ctcimport import ImportCTC
from .operators.cclimport import ImportCCL
from .operators.ctcexport import ExportCTC
from .operators.cclexport import ExportCCL
from .operators.ccltools import MeshFromCapsule,CapsuleFromSelection,DuplicateCapsule
from .operators.ccltools import CopyCCLData, PasteCCLData
from .operators.ccltools import CCLTools
                                 

from .operators.ctcimport import menu_func_import as ctc_import
from .operators.ctcexport import menu_func_export as ctc_export
from .operators.cclimport import menu_func_import as ccl_import
from .operators.cclexport import menu_func_export as ccl_export


classes = [ImportCTC,ExportCTC,ImportCCL,ExportCCL,
           MeshFromCapsule,CapsuleFromSelection,DuplicateCapsule,
           CopyCCLData, PasteCCLData,
           CCLTools]
importFunctions = [ccl_import,ctc_import] 
exportFunctions = [ccl_export,ctc_export] 

def register():
    for cl in classes:
        bpy.utils.register_class(cl)
    for iF in importFunctions:
        bpy.types.INFO_MT_file_import.append(iF)
    for iF in exportFunctions:
        bpy.types.INFO_MT_file_export.append(iF)
    
def unregister():
    for cl in classes:
        bpy.utils.unregister_class(cl)
    for iF in importFunctions:
        bpy.types.INFO_MT_file_import.remove(iF)
    for iF in exportFunctions:
        bpy.types.INFO_MT_file_export.remove(iF)   
    
if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
