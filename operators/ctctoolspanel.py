# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 23:04:20 2019

@author: AsteriskAmpersand
"""

class CTCTools(bpy.types.Panel):
    bl_category = "MHW Physics"
    bl_idname = "panel.mhw_ctc"
    bl_label = "CTC Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    # bl_category = "Tools"

    addon_key = __package__.split('.')[0]

    def draw(self, context):
        addon = context.user_preferences.addons[self.addon_key]
        self.addon_props = addon.preferences
        
        layout = self.layout
        #self.layout.label("CCL Capsule Tools")
        #self.layout.operator("ctc_tools.mesh_from_capsule", icon='MESH_CUBE', text="Mesh from Capsule")
        
        self.draw_edit_matrixes(context, layout)
        layout.separator()
        
    def draw_edit_matrixes(self, context, layout):
        addon_props = self.addon_props

        self.layout.label("Node Linear Structures")
        col = layout.column(align = True)
        row = col.row(align = True)
        row.operator('ctc_tools.get_all_matrices', text = 'Get')
        row.operator('ctc_tools.set_all_matrices', text = 'Set')

        col0 = layout.column(align = True)
        row0 = col0.row(align = True)
        self.layout.label("Rotation Matrix")
        row0.operator('ctc_tools.get_rotation_matrices', text = 'Get')
        row0.operator('ctc_tools.set_rotation_matrices', text = 'Set')
        col0.prop(addon_props, 'rotation_buffer', text = '')

        col1 = layout.column(align = True)
        row1 = col1.row(align = True)
        self.layout.label("Translation Matrix")
        row1.operator('ctc_tools.get_translation_matrices', text = 'Get')
        row1.operator('ctc_tools.set_translation_matrices', text = 'Set')
        col1.prop(addon_props, 'get_translation_buffer', text = '')
        
        col2 = layout.column(align = True)
        row2 = col2.row(align = True)
        self.layout.label("Unknown Vector")
        row2.operator('ctc_tools.get_unknown_vector', text = 'Get')
        row2.operator('ctc_tools.set_unknown_vector', text = 'Set')
        col2.prop(addon_props, 'get_unknown_vector', text = '')
        
        col3 = layout.column(align = True)
        row3 = col3.row(align = True)
        self.layout.label("Unknown Bytes")
        row3.operator('ctc_tools.get_unknown_bytes', text = 'Get')
        row3.operator('ctc_tools.set_unknown_bytes', text = 'Set')
        
        self.layout.label("Chain-wide Data")
        col = layout.column(align = True)
        row = col.row(align = True)
        row.operator('ctc_tools.get_chain_data', text = 'Get')
        row.operator('ctc_tools.set_chain_data', text = 'Set')
        
    def draw_create_tools(self, context, layout):
        self.layout.operator("ctc_tools.create_ctc", icon='MOD_MESHDEFORM', text="Create ")
        self.layout.operator("ctc_tools.chain_from_selection", icon='CONSTRAINT_DATA', text="Chain from Selection")
        self.layout.operator("ctc_tools.extend_chain", icon='CONSTRAINT_DATA', text="Extend Chain")
        self.layout.operator("ctc_tools.change_target", icon='CONSTRAINT_DATA', text="Change Target")
        self.layout.operator("ctc_tools.realign_chain", icon='CONSTRAINT_DATA', text="Reparent Chain")  
        self.layout.operator("ctc_tools.realign_chain", icon='CONSTRAINT_DATA', text="Reroot Chain")  
        self.layout.operator("ctc_tools.realign_chain", icon='MOD_MESHDEFORM', text="Realign Chains with Target")
        self.layout.operator("ctc_tools.find_duplicates", icon='MOD_MESHDEFORM', text="Find Duplicate IDs")  