# map -> blender

# brush planes > convex mesh

# { start entity
# { start brush
# (vertex) (vertex) (vertex) texname xofs yofs rot xscale yscale
# MINIMUM 4 planes
# }
# }

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

from mathutils import (
    Vector,
    geometry,
)
import math

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
    if line is not None:
        point = geometry.intersect_line_plane(line[0], line[0] + line[1], p3c, p3n)
    return point

class MapFace:
    def __init__(self, plane_co, plane_no):
        self.plane_co = plane_co
        self.plane_no = plane_no
        self.verts = []


# add to existing mesh (must already be in edit mode)
def brush_to_mesh(brush_str, mesh):
    # parse planes from brush_str
    bm = bmesh.from_edit_mesh(mesh)
    faces = []
    for plane_str in brush.splitlines():
        plane = get_plane(plane_str)
        face = MapFace(plane[0], plane[1])
        faces.append(face)

    if len(planes) < 4:
        print("ERROR: Number of planes is < 4")
        return

    # for every possible plane intersection, get vertices
    for i1, f1 in faces[:-2]:
        for i2, f2 in faces[i1+1:-1]:
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

    # calculate polygons from verts in each list
    for face in faces:
        num_verts = len(verts)
        if num_verts < 3:
            print("ERROR: Number of vertices < 3")
            continue

        # get average of vertex positions (approx center)
        center = Vector()
        for vert in face.verts:
            center += vert
        center /= num_verts

        # determine winding order of verts using angle between vectors
        angles = [(0, 0.0)] # vertex index, angle
        v1 = (face.verts[0] - center).normalized() # start direction
        for i, vert in face.verts[1:]:
            v2 = (vert - center).normalized()
            angle = v1.angle(v2)
            cross = v1.cross(v2)
            if copysign(1, face.plane_no.dot(cross)) < 0:
                angle += math.pi
            angles.append((i, angle))
            
        # sort indices by angle, then sort face.verts
        angles.sort(key=lamda vert: vert[1])
        verts = [face.verts[v[0]] for v in angles]
        face.verts = verts

        # convert vertices of each face into mesh polygons
        face = bm.faces.new(face.verts)

