import os
import numpy as np
import os

from . import pyrecast as rd

from . import usd_utils
import omni.physx

class NavmeshInterface:
    def __init__(self): 
        self.navmesh = rd.Navmesh()
        self.built = False
        self.input_prim = None
        self.input_vert = None
        self.input_tri = None
        self.random_points = None

    def get_random_points(self, num_points):
        if not self.built:
            return None
        self.random_points = self.navmesh.get_random_points(num_points)
        return self.random_points

    def load_mesh(self, prim):
        self.input_vert, self.input_tri  = usd_utils.parent_and_children_as_mesh(prim)
        self.input_prim = prim

        self.navmesh.load_mesh(self.input_vert, self.input_tri)

    def build_navmesh(self, settings={}):
        self.navmesh.build_navmesh(settings)
        self.built = True

    def find_paths(self, starts, ends):
        paths = self.navmesh.find_paths(starts, ends)
        return paths

    def get_navmesh_raw_contours(self):
        rawvert, rawpolygons, _ = self.navmesh.get_navmesh_raw_contours()
        return rawvert, rawpolygons

    def get_navmesh_contours(self):
        vert, _, _ = self.navmesh.get_navmesh_contours()

        vert = np.asarray(vert).reshape(-1, 3)
        edges = [[i, i+1] for i in range(0, len(vert)-1, 2)]
        self.contour_verts = vert
        self.contour_edges = edges

        return self.contour_verts, self.contour_edges

    def make_walls(self, vertices, edges, height):

        # Extrude the walls up
        vertices = np.array(vertices)  # Ensure vertices are a NumPy array
        extruded_vertices = np.copy(vertices)
        extruded_vertices[:, 1] += height  # Add height to the z-coordinate
        side_triangles = []

        for edge in edges:
            i, j = edge
            A = vertices[i]
            B = vertices[j]
            A_prime = extruded_vertices[i]
            B_prime = extruded_vertices[j]

            triangle1 = [A, B, B_prime]
            triangle2 = [A, B_prime, A_prime]
            side_triangles.extend([triangle1, triangle2])

        # Do the welding and extrusion
        self.side_triangles = side_triangles

        faces = []
        verts = []
        tri = 0
        for i, face in enumerate(side_triangles):
            for v in face:
                verts.append(v)
            faces.append([tri, tri+1, tri+2])
            tri += 3

        # weld faces and vertices to remove duplicates 
        faces = np.asarray(faces)
        v, inverse_indices = np.unique(verts, axis=0, return_inverse=True)
        t = inverse_indices[faces.flatten()].reshape(faces.shape)

        self.wall_v = v
        self.wall_t = t 

        return v, t

    def get_selected_prim(self):
        self.stage = omni.usd.get_context().get_stage()

        # Get the selections from the stage
        self._usd_context = omni.usd.get_context()
        self._selection = self._usd_context.get_selection()
        selected_paths = self._selection.get_selected_prim_paths()
        # Expects a list, so take first selection
        self.input_prim = [self.stage.GetPrimAtPath(x) for x in selected_paths][0]

        return self.input_prim

    def get_navmesh_triangles(self):
        triangles = self.navmesh.get_navmesh_triangles()
        return triangles

    def get_navmesh_polygons(self):
        trivert,_,_ = self.navmesh.get_navmesh_polygons()
        trivert = np.asarray(trivert).reshape(-1,3)

        print(f'Got navmesh')

        v = trivert
        t = []
        for i in range(0, len(trivert), 3):
            t.append([i,i+1,i+2])
        self.navmesh_v = np.array(v, dtype=np.float32)
        self.navmesh_t = np.array(t, dtype=np.int32)
        return self.navmesh_v, self.navmesh_t