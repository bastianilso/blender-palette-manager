bl_info = {  
 "name": "Palette Manager",  
 "author": "Bastian Ilso (bastianilso)",  
 "version": (0, 1),  
 "blender": (2, 7, 8),  
 "location": "Tools Panel -> Tools",  
 "description": "Set up a palette and apply shadeless colors to new objects easily",  
 "warning": "",
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Material"}

import bpy
from bpy.types import Panel, UIList, Operator, PropertyGroup
from bpy.props import IntProperty, FloatProperty, PointerProperty, FloatVectorProperty, CollectionProperty, StringProperty
from mathutils import Color

def apply_material(self, context):
    
    if (bpy.context.selected_objects is None):
        return
    
    scene = bpy.context.scene
    for ob in bpy.context.selected_objects:
        mat_name = 'Palette_ %s' % scene.palette_collection[scene.color_index].name
        color = scene.palette_collection[scene.color_index].color
        bpy.data.materials.new(mat_name)    
        bpy.data.materials[mat_name].diffuse_color = color
        bpy.data.materials[mat_name].diffuse_intensity = 1.0
        bpy.data.materials[mat_name].use_shadeless = True

        if (scene.render.engine == 'CYCLES'):
            bpy.data.materials[mat_name].use_nodes = True
            
            # connect emission node with material output node
            bpy.data.materials[mat_name].node_tree.nodes.new(type='ShaderNodeEmission')
            inp = bpy.data.materials[mat_name].node_tree.nodes['Material Output'].inputs['Surface']
            outp = bpy.data.materials[mat_name].node_tree.nodes['Emission'].outputs['Emission']
            bpy.data.materials[mat_name].node_tree.links.new(inp,outp)

            # connect light path node to emission node
            bpy.data.materials[mat_name].node_tree.nodes.new(type='ShaderNodeLightPath')
            inp = bpy.data.materials[mat_name].node_tree.nodes['Emission'].inputs['Strength']
            outp = bpy.data.materials[mat_name].node_tree.nodes['Light Path'].outputs['Is Camera Ray']
            bpy.data.materials[mat_name].node_tree.links.new(inp,outp)

            bpy.data.materials[mat_name].node_tree.nodes['Emission'].inputs['Color'].default_value = (color.r,color.g,color.b, 1.0)

        ob.data.materials.clear()
        ob.data.materials.append(bpy.data.materials[mat_name])        

class UI:
    bl_category = 'Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'

class PaletteCollectionProperties(bpy.types.PropertyGroup):
    '''name = StringProperty() '''

    id = IntProperty()
        
    color = FloatVectorProperty(
        name="Color",
        description="Color",
        default=(1.0,1.0,1.0),
        subtype="COLOR",
        update=apply_material
        )

class ColorListActions(bpy.types.Operator):
    bl_idname = "palette.list_action"
    bl_label = "List Action"

    action = bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
        )
    )

    def invoke(self, context, event):
        scn = context.scene
        idx = scn.color_index

        if self.action == 'DOWN' and idx < len(scn.palette_collection) - 1:
            item_next = scn.palette_collection[idx+1].name
            scn.color_index += 1

        elif self.action == 'UP' and idx >= 1:
            item_prev = scn.palette_collection[idx-1].name
            scn.color_index -= 1

        elif self.action == 'REMOVE':
            scn.palette_collection.remove(idx)
            scn.color_index -= 1
                            
            if scn.color_index < 0 and len(scn.palette_collection) > 0:
                scn.color_index = 0

        elif self.action == 'ADD':
            item = scn.palette_collection.add()
            item.id = len(scn.palette_collection)-1
            scn.color_index = (len(scn.palette_collection)-1)
            item.name = 'Color %d' % scn.color_index

        return {"FINISHED"}

class ColorItems(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scn = context.scene
        layout.prop(item, "name", text="", emboss=False, translate=False)

    def invoke(self, context, event):
        pass   

class PaletteManager(UI,Panel):
    """Creates a Palette Manager in the Tools panel"""
    bl_label = 'Palette Manager'
    bl_idname = 'tools_palette_manager'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        rows = 2
        row = layout.row()
        row.template_list("ColorItems", "", scene, "palette_collection", scene, "color_index", rows=rows)

        col = row.column(align=True)
        col.operator("palette.list_action", icon='ZOOMIN', text="").action = 'ADD'
        col.operator("palette.list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
        col.separator()
        col.operator("palette.list_action", icon='TRIA_UP', text="").action = 'UP'
        col.operator("palette.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

        if scene.color_index > -1:
            row = layout.row()
            row.prop(scene.palette_collection[scene.color_index], "name", text="")
            split = row.split()
            split.prop(scene.palette_collection[scene.color_index], "color", text="")

classes = (
    PaletteManager,
    PaletteCollectionProperties,
    ColorListActions,
    ColorItems,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.palette_collection = CollectionProperty(type=PaletteCollectionProperties)
    bpy.types.Scene.color_index = IntProperty(update=apply_material)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
