import omni.ext
import omni.ui as ui
from pxr import Gf

from . import core
from . import usd_utils

import numpy as np


class SiborgCreateNavmeshExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[siborg.create.navmesh] siborg create navmesh startup")

        self._window = ui.Window("Navmesh Demo", width=300, height=300)
        with self._window.frame:
            with ui.VStack():

                self.navmesh = core.NavmeshInterface()

                def assign_mesh():
                    # get the selected prim
                    prim_selected = self.navmesh.get_selected_prim()

                    # load the mesh
                    self.navmesh.load_mesh(prim_selected)

                def build_navmesh():
                    # build the navmesh
                    self.navmesh.build_navmesh()

                def get_random_points():
                    # get random points
                    if not self.navmesh.built:
                        print('Navmesh not built')
                        return
                    pnts = self.navmesh.get_random_points(10)

                    # plot points
                    usd_utils.create_geompoints(pnts)

                def get_path():
                    # get sample path
                    path_pnts = self.navmesh.find_paths([self.navmesh.random_points[0]], 
                                                        [self.navmesh.random_points[1]])
                    path_pnts = np.asarray(path_pnts).reshape(-1, 3)

                    # plot the path
                    usd_utils.create_curve(path_pnts)

                def visualize_navmesh(): 
                    # get the navmesh triangles
                    if self.navmesh.built:
                        v, t, = self.navmesh.get_navmesh_polygons()
                        v = v.flatten()
                        # create a usd color of blue with transparency
                        color = Gf.Vec3f(0.051208995, 0.774935, 0.94585985)
                        opacity = 0.89
                        usd_utils.create_mesh('/World/navmeshmesh', v, t, color, opacity)
                    else:
                        print('Navmesh not built')  

                def get_outline():
                    self.navmesh.get_navmesh_contours()
                    # plot the outline

                def make_walls():
                    self.navmesh.make_walls(self.navmesh.contour_verts, self.navmesh.contour_edges, 3)

                def visualize_walls():
                        v = self.navmesh.wall_v.flatten()
                        t = self.navmesh.wall_t 
                        # create a usd color of blue with transparency
                        color = Gf.Vec3f(0.30877593, 0.64968157, 0.18828352)
                        opacity = 0.89
                        usd_utils.create_mesh('/World/navmeshwalls', v, t, color, opacity)


                with ui.VStack():
                    ui.Button("Assign Mesh", clicked_fn=assign_mesh)
                    ui.Button("Build Navmesh", clicked_fn=build_navmesh)
                    ui.Button("Get Random Points", clicked_fn=get_random_points)
                    ui.Button("Get Path", clicked_fn=get_path)
                    ui.Button("Create Mesh", clicked_fn=visualize_navmesh)
                    ui.Button("Get Outline", clicked_fn=get_outline)
                    ui.Button("Build Walls", clicked_fn=make_walls)
                    ui.Button("Make Walls", clicked_fn=visualize_walls)


    def on_shutdown(self):
        print("[siborg.create.navmesh] siborg create navmesh shutdown")
