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
    "version": (2,0,0),
    "blender": (2,80,0)
}
 
import bpy

from .operators.ctcimport import ImportCTC
from .operators.cclimport import ImportCCL
from .operators.ctcexport import ExportCTC
from .operators.cclexport import ExportCCL
from .operators.ccltools import MeshFromCapsule,CapsuleFromSelection,DuplicateCapsule
from .operators.ccltools import CopyCCLData, PasteCCLData, CCLTools
from .operators.ctctools import (findDuplicates, realignChain, changeNodeTarget,
                                 reendChain, restartChain, extendChain,
                                 createCTC, chainFromSelection)
from .operators.ctctoolspanel import CTCTools
from .operators.ctcmatrixtools import (get_all_matrices,set_all_matrices,
                                        get_rotation_matrices,set_rotation_matrices,
                                        get_translation_matrices,set_translation_matrices,
                                        get_unknown_vector,set_unknown_vector,
                                        get_unknown_bytes,set_unknown_bytes,
                                        get_chain_data,set_chain_data)
from .operators.ctcpreferences import CTCPrefs

from .operators.ctcimport import menu_func_import as ctc_import
from .operators.ctcexport import menu_func_export as ctc_export
from .operators.cclimport import menu_func_import as ccl_import
from .operators.cclexport import menu_func_export as ccl_export

from .operators.selection import Selection

classes = [Selection,
           ImportCTC,ExportCTC,ImportCCL,ExportCCL,
           MeshFromCapsule,CapsuleFromSelection,DuplicateCapsule,
           CopyCCLData, PasteCCLData,
           CCLTools,CTCTools,CTCPrefs,
           findDuplicates, realignChain, changeNodeTarget,
           reendChain, restartChain, extendChain,
           createCTC, chainFromSelection,
           get_all_matrices,set_all_matrices,
           get_rotation_matrices,set_rotation_matrices,
           get_translation_matrices,set_translation_matrices,
           get_unknown_vector,set_unknown_vector,
           get_unknown_bytes,set_unknown_bytes,
           get_chain_data,set_chain_data,]
importFunctions = [ccl_import,ctc_import] 
exportFunctions = [ccl_export,ctc_export] 

def register():
    for cl in classes:
        bpy.utils.register_class(cl)
    for iF in importFunctions:
        bpy.types.TOPBAR_MT_file_import.append(iF)
    for iF in exportFunctions:
        bpy.types.TOPBAR_MT_file_export.append(iF)
    
def unregister():
    for cl in classes:
        bpy.utils.unregister_class(cl)
    for iF in importFunctions:
        bpy.types.TOPBAR_MT_file_import.remove(iF)
    for iF in exportFunctions:
        bpy.types.TOPBAR_MT_file_export.remove(iF)   
    
if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
