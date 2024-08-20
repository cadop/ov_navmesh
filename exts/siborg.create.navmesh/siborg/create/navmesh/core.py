from collections import defaultdict
import os
import numpy as np
import os

from . import pyrecast as rd

from . import usd_utils
import omni.physx

class NavmeshInterface:
    def __init__(self, up_axis='Y'): 
        self.navmesh = rd.Navmesh()
        self.built = False
        self.input_prim = None
        self.input_vert = None
        self.input_tri = None
        self.random_points = None
        self.wall_outline = []

        # if z_up is true, we will need to do some conversion before sending to 
        # recast, then, we will convert it back to y_up (all functions will need to do that)
        if up_axis == 'Z': self.z_up = True
        else: self.z_up = False  

    def _convert_up_axis(self, vertices, inverse=False):
        '''
        Convert all data between navmesh interface and end-user to be in the correct up axis

        pyrecast assumes y-up, so only change when z-up is true
        inverse = True will convert y-up output back to z-up
        '''
        if self.z_up == False:
            return vertices
        
        vertices = np.array(vertices)
        v_copy = np.copy(vertices)
        if inverse:
            # Convert data we have been given in y-up into the z-up of scene (e.g. output from recast)
            v_copy[:, 0], v_copy[:, 1], v_copy[:, 2] = vertices[:, 0], -vertices[:, 2], vertices[:, 1]
        else: 
            # Convert the up axis from Y to Z
            v_copy[:, 0], v_copy[:, 1], v_copy[:, 2] = vertices[:, 0], vertices[:, 2], -vertices[:, 1]

        vertices = v_copy
        return vertices

    def get_random_points(self, num_points):
        if not self.built:
            return None
        self.random_points = self.navmesh.get_random_points(num_points)
        
        # Check if we need to convert the up axis
        self.random_points = self._convert_up_axis(self.random_points, inverse=True)
        
        return self.random_points

    def load_mesh(self, prim):
        self.input_vert, self.input_tri  = usd_utils.parent_and_children_as_mesh(prim)
        self.input_prim = prim
        
        self.input_vert = self._convert_up_axis(self.input_vert)

        self.navmesh.load_mesh(self.input_vert, self.input_tri)

    def build_navmesh(self, settings={}):
        self.navmesh.build_navmesh(settings)
        self.built = True

    def find_paths(self, starts, ends):

        starts = [self._convert_up_axis(starts)]
        ends = [self._convert_up_axis(ends)]

        paths = self.navmesh.find_paths(starts, ends)
        path_pnts = np.asarray(paths).reshape(-1, 3)
        path_pnts = self._convert_up_axis(path_pnts, inverse=True)

        return path_pnts

    def get_navmesh_raw_contours(self):
        rawvert, rawpolygons, _ = self.navmesh.get_navmesh_raw_contours()
        rawvert = self._convert_up_axis(rawvert, inverse=True)
        return rawvert, rawpolygons

    def get_navmesh_contours(self):
        vert, _, _ = self.navmesh.get_navmesh_contours()

        vert = np.asarray(vert).reshape(-1, 3)
        # Convert if needed
        vert = self._convert_up_axis(vert, inverse=True)
        
        edges = [[i, i+1] for i in range(0, len(vert)-1, 2)]
        self.contour_verts = vert
        self.contour_edges = edges

        return self.contour_verts, self.contour_edges

    def make_walls(self, vertices, edges, height):

        # Extrude the walls up
        vertices = np.array(vertices)  # Ensure vertices are a NumPy array
        vertices = self._convert_up_axis(vertices)
        extruded_vertices = np.copy(vertices)
        extruded_vertices[:, 1] += height  # Add height to the z-coordinate
        side_triangles = []

        # Go through each edge and create two triangles (square wall)
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
        # Make faces
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

    def make_outline(self):
        # Go through the edges and make individual lines, it is what it is

        width = np.array([0.2], dtype=float)
        color = (0.8,0.8,0.8)

        # contour_edges = np.array(self.contour_edges)
        # v, inverse_indices = np.unique(self.contour_verts, axis=0, return_inverse=True)
        # e = inverse_indices[contour_edges.flatten()]
        # e2 = e.reshape(contour_edges.shape)
        # e3 = np.sort(e2, axis=1)

        # # Use a set to keep track if a vertex is in the contour
        # vertex_sets = []

        for idx, edge in enumerate(self.contour_edges):
            i, j = edge
            A = self.contour_verts[i]
            B = self.contour_verts[j]
            self.wall_outline.append([tuple(A), tuple(B)])

            # for jdx, vertex in enumerate([A, B]):
            #     if vertex not in vertex_sets:
            #         vertex_sets.append(vertex)

        # curves = defaultdict(list)
        # curve_names = []

        # # Traverse edges, append to a list, and make a new list when a discontinuity is found
        # for idx, edge in enumerate(self.wall_outline):
        #     # check if the next edge is a discontinuity by it not having the same vertex as the current edge
        #     if idx == 0:
        #         curves[idx].extend(edge)
        #         curve_names.append(idx)
        #         continue
        #     if (edge[0] not in curves[curve_names[-1]]) and (edge[1] not in curves[curve_names[-1]]):

        #         curves[idx].extend(edge)
        #         curve_names.append(idx)
        #     else:
        #         curves[curve_names[-1]].extend(edge)


        # print(curves)

        for idx, curve in enumerate(self.wall_outline):
            usd_utils.create_curve(curve, prim_path=f"/World/Outline/WallOutline{idx}", width=width, color=color)

    def get_selected_prim(self):
        self.stage = omni.usd.get_context().get_stage()

        # Get the selections from the stage
        self._usd_context = omni.usd.get_context()
        self._selection = self._usd_context.get_selection()
        selected_paths = self._selection.get_selected_prim_paths()
        # Expects a list, so take first selection
        self.input_prim = [self.stage.GetPrimAtPath(x) for x in selected_paths]

        self.input_vert, self.input_tri = usd_utils.get_all_stage_mesh(self.stage , self.input_prim)

        if len(self.input_vert) == 0:
            print('No mesh found')
            return False
        
        #Convert the up axis if needed
        self.input_vert = self._convert_up_axis(self.input_vert)
        
        self.navmesh.load_mesh(self.input_vert, self.input_tri)
        return True

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

        self.navmesh_v = self._convert_up_axis(self.navmesh_v, inverse=True)

        return self.navmesh_v, self.navmesh_t