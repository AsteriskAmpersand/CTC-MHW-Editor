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
from .operators.cclexport import ExportCCL
from .operators.ctcimport import menu_func_import as ctc_import
from .operators.cclimport import menu_func_import as ccl_import
from .operators.cclexport import menu_func_export as ccl_export

def register():
    bpy.utils.register_class(ImportCTC)
    bpy.types.INFO_MT_file_import.append(ctc_import)
    bpy.utils.register_class(ImportCCL)
    bpy.types.INFO_MT_file_import.append(ccl_import)
    bpy.utils.register_class(ExportCCL)
    bpy.types.INFO_MT_file_export.append(ccl_export)
    
def unregister():
    bpy.utils.unregister_class(ImportCTC)
    bpy.types.INFO_MT_file_import.remove(ctc_import)
    bpy.utils.unregister_class(ImportCCL)
    bpy.types.INFO_MT_file_import.remove(ccl_import)
    bpy.utils.unregister_class(ExportCCL)
    bpy.types.INFO_MT_file_export.remove(ccl_export)
    
if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
