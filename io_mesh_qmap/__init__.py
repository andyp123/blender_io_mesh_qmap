#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

# reload submodules if the addon is reloaded 
if "bpy" in locals():
    import importlib
    importlib.reload(map_importer)

# addon information
bl_info = {
    "name": "Import Quake MAP format",
    "author": "Andrew Palmer",
    "version": (0,1),
    "blender": (2, 80, 0),
    "location": "File > Import > Quake MAP (.map)",
    "description": "Import geometry from a Quake 1 MAP file.",
    "wiki_url": "https://github.com/andyp123/blender_io_mesh_qmap",
    "category": "Import-Export",
}

# imports
import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator
from . import map_importer
import time

# main code
class MAPImporter(bpy.types.Operator, ImportHelper):
    bl_idname       = "map_importer.map"
    bl_description  = "Import geometry from Quake MAP file format (.map)"
    bl_label        = "Quake MAP Importer"
    bl_options      = {'UNDO'}

    filename_ext = ".map"
    filter_glob: StringProperty(
        default="*.map",
        options={'HIDDEN'},
        )

    scale: FloatProperty(
        name="Scale",
        description="Adjust the size of the imported geometry",
        min=0.0, max=1.0,
        soft_min=0.0, soft_max=1.0,
        default=0.03125, # 1 Meter = 32 Quake units
        )

    worldspawn_only: BoolProperty(
        name="Worldspawn Only",
        description="Import only the main map geometry and ignore other models, such as doors, etc",
        default=False,
        )
        
    ignore_clip: BoolProperty(
        name="Ignore Clip Brushes",
        description="Ignore clip brushes",
        default=True,
        )
        
    ignore_triggers: BoolProperty(
        name="Ignore Triggers",
        description="Ignore trigger entities",
        default=True,
        )
    
    def execute(self, context):
        time_start = time.time()
        options = {
            'scale' : self.scale,
            'worldspawn_only' : self.worldspawn_only,
            'ignore_clip' : self.ignore_clip,
            'ignore_triggers' : self.ignore_triggers,
            }
        map_importer.import_map(context, self.filepath, options)
        print("Elapsed time: %.2fs" % (time.time() - time_start))
        return {'FINISHED'}


classes = (
    MAPImporter,
)

def menu_func(self, context):
    self.layout.operator(MAPImporter.bl_idname, text="Quake MAP (.map)")


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)

    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
