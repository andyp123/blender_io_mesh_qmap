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
# Andrew Palmer (andyp.123@gmail.com)

import bpy, bmesh
from mathutils import (
    Vector,
    geometry,
)
import math
import time


# 1/32 to convert Quake scale to meters
# This will be overriden by importer options
map_scale = 0.03125


class MapFace:
    def __init__(self, plane_co, plane_no):
        self.plane_co = plane_co
        self.plane_no = plane_no
        # self.verts = []


def get_plane (face_str):
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


# Add to existing mesh (must already be in edit mode)
def brush_to_mesh(brush_str, bm, entity_num = -1, brush_num = -1):
    # Parse planes from brush_str
    faces = []
    for plane_str in brush_str.splitlines():
        plane = get_plane(plane_str)
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
    epsilon = 0.1
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
            
    # Add valid verts to the bmesh
    new_verts = [None] * len(valid_verts)
    for i, vert in enumerate(valid_verts):
        new_verts[i] = bm.verts.new(vert * map_scale)
    bmesh.ops.convex_hull(bm, input=new_verts, use_existing_faces=True)
    

def map_to_mesh(map_str, worldspawn_only = False):
    # Find first entity
    i0 = map_str.find('{')
    
    entities = []
    entity_num = 0
    
    while i0 != -1:
        # Is there a brush?
        i1 = map_str.find('}', i0 + 1)
        i2 = map_str.find('{', i0 + 1)
        
        obj = None
        mesh = None
        bm = None
        brush_num = 0
        
        # Add all brushes for the current entity to the mesh, ignoring triggers
        if map_str.find('"classname" "trigger_', i0, i2) == -1:
            # i2 < i1 means i1 is the end of a brush
            # i2 > i1 means i1 is the end of an entity
            while i2 < i1 and i2 != -1:
                brush_str = map_str[i2 + 1: i1].strip()
                
                # Convert brush to mesh, ignoring clip brushes
                if brush_str.find(' clip ') == -1:
                    if mesh is None:
                        # Create a mesh to add this brush to if one doesn't exist
                        if bpy.context.active_object:
                            bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.add(type='MESH', enter_editmode=True)
                        obj = bpy.context.object
                        obj.name = str(entity_num)
                        mesh = obj.data
                        mesh.name = obj.name
                        bm = bmesh.from_edit_mesh(mesh)
                                        
                    brush_to_mesh(brush_str, bm, entity_num, brush_num)
                
                i2 = map_str.find('{', i1 + 1)
                i1 = map_str.find('}', i1 + 1)
                brush_num += 1
        
        if mesh is not None:
            bmesh.update_edit_mesh(mesh)
            entities.append(obj)
        
        # Move to next entity
        if worldspawn_only:
            break
        i0 = map_str.find('{', i1 + 1)
        entity_num += 1
        
    return entities


def post_process(entities):
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Select meshes to set origin to bounding box center
    # Leave worldspawn origin at 0,0,0
    for obj in entities[1:]:
        obj.select_set(True)
        
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in entities:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(obj.location))
        root = bpy.context.active_object
        root.name = "entity_" + obj.name
        obj.name += ".000"
        obj.data.name = obj.name
        
        # Separate mesh into sub objects
        root.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Convert to quads (using face 40d and shape 90d) and separate
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.tris_convert_to_quads(face_threshold=0.698132, shape_threshold=1.5708)
        bpy.ops.mesh.separate(type='LOOSE')
        
        # Set parents and bounds
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.context.view_layer.objects.active = root
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        for sub_obj in bpy.context.selected_objects:
            if len(sub_obj.data.vertices) < 4:
                # Delete objects with less than 4 vertices as they can't be a full convex object
                # (occasionally get floating verts, etc.)
                bpy.data.objects.remove(sub_obj, do_unlink=True)


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
        
        time_start = time.time()
        entity_meshes = map_to_mesh(file.read(), options['worldspawn_only'])
        print("Mesh conversion complete: %.2fs" % (time.time() - time_start))
        
        if options['post_process']:
            time_start = time.time()
            post_process(entity_meshes)
            print("Post processing complete: %.2fs" % (time.time() - time_start))
    
    bpy.ops.object.mode_set(mode='OBJECT')

    print("-- IMPORT COMPLETE --")
