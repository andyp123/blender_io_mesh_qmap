# // ENTITY
# {
# "classname" "worldspawn"
# "message" "Pretend Dead Friend"
# "worldtype" "0"
# "sounds" "7"
# // BRUSH
# {
# ( 128 -32 0 ) ( 96 -16 0 ) ( 224 112 0 ) wswamp2_1 0 0 0 1.000000 1.000000
# ( 96 -16 -320 ) ( 128 -32 -320 ) ( 224 64 -320 ) wswamp2_1 0 0 0 1.000000 1.000000
# ( 224 112 -320 ) ( 224 112 0 ) ( 96 -16 0 ) wswamp2_1 0 0 0 1.000000 1.000000
# ( 128 -32 -320 ) ( 128 -32 0 ) ( 224 64 0 ) wswamp2_1 12 0 0 0.750000 1.000000
# ( 224 64 -320 ) ( 224 64 0 ) ( 224 112 0 ) wswamp2_1 0 0 0 1.000000 1.000000
# ( 96 -16 -320 ) ( 96 -16 0 ) ( 128 -32 0 ) wswamp2_1 0 0 0 1.000000 1.000000
# }
# }

import bpy, bmesh
from mathutils import (
    Vector,
    geometry,
)
import math


class MapFace:
    def __init__(self, plane_co, plane_no):
        self.plane_co = plane_co
        self.plane_no = plane_no
        self.verts = []


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


# add to existing mesh (must already be in edit mode)
def brush_to_mesh(brush_str, mesh):
    # parse planes from brush_str
    bm = bmesh.from_edit_mesh(mesh)
    faces = []
    for plane_str in brush_str.splitlines():
        plane = get_plane(plane_str)
        face = MapFace(plane[0], plane[1])
        faces.append(face)

    if len(faces) < 4:
        print("ERROR: Number of planes is < 4")
        return

    # for every possible plane intersection, get vertices
    all_verts = [] # DEBUG
    for i1, f1 in enumerate(faces[:-2]):
        for i2, f2 in enumerate(faces[i1+1:-1]):
            for f3 in faces[i2+1:]:
                vert = intersect_plane_plane_plane(
                    f1.plane_co, f1.plane_no,
                    f2.plane_co, f2.plane_no,
                    f3.plane_co, f3.plane_no
                    )
                if vert is not None:
                    f1.verts.append(vert)
                    f2.verts.append(vert)
                    f3.verts.append(vert)
                    all_verts.append(vert)
    
    # Quick test to make sure vertex positions are correct
    print(len(all_verts))
    
    bm_verts = []
    for vert in all_verts:
        bm_verts.append(bm.verts.new(vert))
    bmesh.update_edit_mesh(mesh)

    for vert in bm.verts:
        vert.select_set(True)
        
    bpy.ops.mesh.convex_hull()

#    # calculate polygons from verts in each list
#    for face in faces:
#        num_verts = len(face.verts)
#        if num_verts < 3:
#            print("ERROR: Number of vertices < 3")
#            continue

#        # get average of vertex positions (approx center)
#        center = Vector()
#        for vert in face.verts:
#            center += vert
#        center /= num_verts

#        # determine winding order of verts using angle between vectors
#        angles = [(0, 0.0)] # vertex index, angle
#        v1 = (face.verts[0] - center).normalized() # start direction
#        for i, vert in enumerate(face.verts[1:]):
#            v2 = (vert - center).normalized()
#            angle = v1.angle(v2)
#            cross = v1.cross(v2)
#            if math.copysign(1, face.plane_no.dot(cross)) < 0:
#                angle += math.pi
#            angles.append((i, angle))
#            
#        # sort indices by angle, then sort face.verts
#        angles.sort(key=lambda vert: vert[1])
#        verts = [face.verts[v[0]] for v in angles]
#        face.verts = verts

#        # convert vertices of each face into mesh polygons
#        bm_verts = []
#        for vert in face.verts:
#            bm_verts.append(bm.verts.new(vert))
#        face = bm.faces.new(bm_verts)
#        
#        bmesh.update_edit_mesh(mesh)


# brush data as a string
test_data = """( 128 64 48 ) ( 160 64 -16 ) ( 160 -0 -16 ) __TB_empty -0 -0 -0 1 1
( 160 -32 -16 ) ( 96 -32 -16 ) ( 128 -32 48 ) __TB_empty -0 -0 -0 1 1
( 128 64 48 ) ( 96 64 -16 ) ( 160 64 -16 ) __TB_empty -0 -0 -0 1 1
( 160 64 -16 ) ( 96 64 -16 ) ( 96 -0 -16 ) __TB_empty -0 -0 -0 1 1
( 96 -0 -16 ) ( 96 64 -16 ) ( 128 64 48 ) __TB_empty -0 -0 -0 1 1"""

def test_function():
    # create mesh and switch to edit mode
    if bpy.context.active_object:
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.add(type='MESH', enter_editmode=True)
    obj = bpy.context.object
    mesh = obj.data
    # try adding the faces of the test_data
    brush_to_mesh(test_data, mesh)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
test_function()
