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


# Author
# Andrew Palmer 
# Github: https://github.com/andyp123/blender_io_mesh_qmap

import bpy, bmesh
from mathutils import (
    Vector,
    geometry,
    Matrix,
)
import math
import time
import os


# 1/32 to convert Quake scale to meters
# This will be overriden by importer options
map_scale = 0.03125

# Dictionary of materials properties
material_definitions = {
    # entity type
    "worldspawn": { "color": (1.0, 1.0, 1.0, 1.0) },
    "solident": { "color": (0.5, 0.5, 0.5, 1.0) },
    "trigger": { "color": (0.7, 0.4, 0.8, 0.5) },
    # brush type (overrides entity type, except for triggers)
    "clip": { "color": (1.0, 0.0, 0.0, 0.5) },
    "water": { "color": (0.0, 0.7, 1.0, 0.7) },
    "lava": { "color": (1.0, 0.3, 0.0, 0.8) },
    "slime": { "color": (0.1, 0.8, 0.2, 0.8) },
    "sky": { "color": (0.2, 0.5, 1.0, 1.0) },
    "hint": { "color": (1.0, 1.0, 0.0, 0.5) },
}

# Actual materials stored here
materials = {}

def create_materials():
    for name, matdef in material_definitions.items():
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = matdef["color"]
        mat.use_backface_culling = True
        materials[name] = mat


def get_material_from_texname(texname, entity_type):
    key = entity_type
    
    if entity_type != 'trigger':
        if texname == 'clip':
            key = 'clip'
        elif texname.startswith('sky'):
            key = 'sky'
        elif texname.startswith('hint'):
            key = 'hint'
        elif texname.startswith('*'):
            if texname.startswith('*lava'):
                key = 'lava'
            elif texname.startswith('*slime'):
                key = 'slime'
            else:
                key = 'water'
            
    return materials.get(key, materials['worldspawn'])


class MapFace:
    def __init__(self, plane_co, plane_no):
        self.plane_co = plane_co
        self.plane_no = plane_no
        # self.verts = []


def get_plane(face_str):
    # get vectors that define the plane
    i0 = face_str.find('(')
    i1 = face_str.find(')')
    v1 = Vector([float(f) for f in face_str[i0+1:i1].split(' ') if f != ''])
    i0 = face_str.find('(', i1)
    i1 = face_str.find(')', i0)
    v2 = Vector([float(f) for f in face_str[i0+1:i1].split(' ') if f != ''])
    i0 = face_str.find('(', i1)
    i1 = face_str.find(')', i0)
    v3 = Vector([float(f) for f in face_str[i0+1:i1].split(' ') if f != ''])
    # return plane_coord, plane_normal
    return (v1, (v1-v2).cross(v3-v2).normalized())


def intersect_plane_plane_plane(p1c, p1n, p2c, p2n, p3c, p3n):
    point = None
    line = geometry.intersect_plane_plane(p1c, p1n, p2c, p2n)
    if line is not None and line[0] is not None:
        point = geometry.intersect_line_plane(line[0], line[0] + line[1], p3c, p3n)
    return point


def get_texname_from_face(face_str):
    i0 = face_str.rfind(')') + 2
    i1 = face_str.find(' ', i0)
    texname = face_str.substring(i0, i1)   


# Convert brush string into a new mesh object
def brush_to_mesh(brush_str, entity_num = -1, brush_num = -1):
    # Parse planes from brush_str
    faces = []
    for face_str in brush_str.splitlines():
        plane = get_plane(face_str)
        face = MapFace(plane[0], plane[1])
        faces.append(face)

    if len(faces) < 4:
        print("ERROR (Entity {}, Brush {}): Number of planes is < 4".format(entity_num, brush_num))
        print(brush_str)
        return

    # For every possible plane intersection, get vertices
    all_verts = []
    for i1, f1 in enumerate(faces[:-2]):
        for i2, f2 in enumerate(faces[i1+1:-1]):
            for f3 in faces[i2+2:]:
                vert = intersect_plane_plane_plane(
                    f1.plane_co, f1.plane_no,
                    f2.plane_co, f2.plane_no,
                    f3.plane_co, f3.plane_no
                    )
                if vert is not None:
                    all_verts.append(vert)
        
    # Check each vert is on or inside the convex volume
    valid_verts = []
    epsilon = 0.1 # TODO: What is the optimal value for epsilon?
    for i, vert in enumerate(all_verts):
        add_vert = True
        for face in faces:
            dis = vert - face.plane_co
            dot = dis.dot(face.plane_no)
            if dot > epsilon:
                add_vert = False
                # print("dot [X]: " + str(dot))
                break
            # print("dot [ ]: " + str(dot))
        if add_vert:
            valid_verts.append(vert)
            
    if len(valid_verts) < 4:
        print("ERROR (Entity {2}, Brush {3}): Only {0} valid vertices found of {1} total".format(
            len(valid_verts), len(all_verts), entity_num, brush_num))
        print(brush_str)
        return
                
    # Add valid verts to a bmesh and run convex operation on them
    bm = bmesh.new()
    for vert in valid_verts:
        bm.verts.new(vert * map_scale)
    bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    
    # Remove loose vertices and convert to quads
    # TODO
    
    # Recalculate the mesh and clean up the bmesh
    # Name of the object is the same format as that used by Trenchbroom obj exporter
    dataname = "entity{}_brush{}".format(entity_num, brush_num)
    me = bpy.data.meshes.new(dataname)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(dataname, me)
    
    return ob
    

def map_to_mesh(map_str, map_name, options):
    worldspawn_only = options['worldspawn_only']
    ignore_clip = options['ignore_clip']
    ignore_hint = options['ignore_hint']
    ignore_triggers = options['ignore_triggers']
    
    # Find first entity
    i0 = map_str.find('{')
    
    entities = []
    entity_num = 0
    
    while i0 != -1:
        # Is there a brush?
        i1 = map_str.find('}', i0 + 1)
        i2 = map_str.find('{', i0 + 1)

        brushes = []
        brush_num = 0
        
        # Add all brushes for the current entity to the mesh, ignoring triggers
        # Get the classname (ni = name index)
        ni0 = map_str.find('"classname" "', i0, i2)
        ni1 = map_str.find('"', ni0 + 13) # ["classname" "] is 13 chars
        classname = "" if (ni0 == -1 or ni1 == -1) else map_str[ni0 + 13 : ni1]
        is_trigger = True if classname.startswith('trigger') else False
        
        entity_type = 'worldspawn' if entity_num == 0 \
            else ('trigger' if is_trigger else 'solident')
  
        if not is_trigger or ignore_triggers is False:
            # i2 < i1 means i1 is the end of a brush
            # i2 > i1 means i1 is the end of an entity
            while i2 < i1 and i2 != -1:
                brush_str = map_str[i2 + 1 : i1].strip()
                # Get the texture name
                ni0 = brush_str.find('\n') # get end of first line
                ni0 = brush_str.rfind(')', 0, ni0 - 1)
                ni1 = brush_str.find(' ', ni0 + 2)
                texname = "" if (ni0 == -1 or ni1 == 1) else brush_str[ni0 + 2: ni1]
                
                # Convert brush to mesh, ignoring clip brushes
                if (texname != 'clip' or ignore_clip is False) and (not texname.startswith('hint') or ignore_hint is False):
                    brush = brush_to_mesh(brush_str, entity_num, brush_num)
                    if brush is not None:
                        mat = get_material_from_texname(texname, entity_type)
                        brush.color = mat.diffuse_color
                        brush.data.materials.append(mat)
                        brushes.append(brush)
                
                i2 = map_str.find('{', i1 + 1)
                i1 = map_str.find('}', i1 + 1)
                brush_num += 1
        
        if len(brushes) > 0:
            entities.append(brushes)
        
        # Move to next entity
        if worldspawn_only:
            break
        i0 = map_str.find('{', i1 + 1)
        entity_num += 1

    # Create collection and link created objects to the scene
    # TODO: Group entities
    if len(entities) > 0:
        global_matrix = Matrix()
        collection = bpy.data.collections.new(map_name)
        bpy.context.scene.collection.children.link(collection)
        
        for entity in entities:
            for brush in entity:
                collection.objects.link(brush)
                brush.matrix_world = global_matrix


def import_map(context, filepath, options):
    with open(filepath, 'rt') as file:
        map_scale = options['scale']

        print("-- IMPORTING MAP --")
        print("Source file: %s" % (filepath))
        
        # Clear selection and reset cursor to prevent weirdness
        if bpy.context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.cursor.location = ((0,0,0))
        bpy.context.scene.cursor.rotation_euler = ((0,0,0))
        
        map_name = os.path.basename(filepath).split('.')[0] + "_map"
        
        time_start = time.time()
        create_materials()
        entity_meshes = map_to_mesh(file.read(), map_name, options)
        print("Mesh conversion complete: %.2fs" % (time.time() - time_start))

    print("-- IMPORT COMPLETE --")
