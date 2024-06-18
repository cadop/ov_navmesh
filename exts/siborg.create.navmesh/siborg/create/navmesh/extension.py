import omni.ext
import omni.ui as ui
from pxr import Gf

from . import core
from . import usd_utils

import numpy as np

from omni.ui import color as cl

class SiborgCreateNavmeshExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[siborg.create.navmesh] siborg create navmesh startup")

        self._window = ui.Window("Navmesh", width=300, height=300)

        # colors 
        s_red = {"background_color": cl(160,0,0)}
        s_yellow = {"background_color": cl(150,150,0)}
        s_green = {"background_color": cl(0,160,0)}
        s_done = {"background_color": cl(0,160,0, 80)}

        
        with self._window.frame:
            with ui.VStack():

                self.navmesh = core.NavmeshInterface()

                def reset_btns():
                    self.assign_btn.style = s_yellow
                    self.bld_btn.style = s_red
                    self.rnd_pnts_btn.style = s_red
                    self.rnd_pth_btn.style = s_red
                    self.mesh_btn.style = s_red
                    self.getout_btn.style = s_red
                    self.mke_out_btn.style = s_red
                    self.bld_wall_btn.style = s_red
                    self.make_wall_btn.style = s_red


                def assign_mesh():
                    # get the selected prim
                    # load the mesh
                    reset_btns()
                    if self.navmesh.get_selected_prim():
                        self.assign_btn.style = s_done
                        self.bld_btn.style = s_yellow

                def build_navmesh():
                    # build the navmesh
                    self.navmesh.build_navmesh()
                    self.bld_btn.style = s_done
                    self.rnd_pnts_btn.style = s_green
                    self.rnd_pth_btn.style = s_green
                    self.mesh_btn.style = s_yellow    
                    self.getout_btn.style = s_yellow


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
                    s,e = self.navmesh.get_random_points(2)

                    path_pnts = self.navmesh.find_paths([s], [e])
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
                        self.mesh_btn.style = s_done
                    else:
                        print('Navmesh not built')  
                        reset_btns()

                def get_outline():
                    self.navmesh.get_navmesh_contours()
                    self.getout_btn.style = s_done
                    self.mke_out_btn.style = s_yellow
                    # plot the outline

                def make_outline():
                    self.navmesh.make_outline()
                    self.mke_out_btn.style = s_done


                def make_walls():
                    self.navmesh.make_walls(self.navmesh.contour_verts, self.navmesh.contour_edges, 3)
                    self.bld_wall_btn.style = s_done
                    self.make_wall_btn.style = s_yellow

                def visualize_walls():
                    v = self.navmesh.wall_v.flatten()
                    t = self.navmesh.wall_t 
                    # create a usd color of blue with transparency
                    color = Gf.Vec3f(0.30877593, 0.64968157, 0.18828352)
                    opacity = 0.89
                    usd_utils.create_mesh('/World/navmeshwalls', v, t, color, opacity)
                    self.make_wall_btn.style = s_done


                with ui.VStack():
                    self.assign_btn = ui.Button("Assign Mesh", clicked_fn=assign_mesh, style=s_yellow)
                    self.bld_btn = ui.Button("Build Navmesh", clicked_fn=build_navmesh, style=s_red)
                    self.rnd_pnts_btn = ui.Button("Get Random Points", clicked_fn=get_random_points, style=s_red)
                    self.rnd_pth_btn = ui.Button("Get Random Path", clicked_fn=get_path, style=s_red)
                    self.mesh_btn = ui.Button("Create Mesh", clicked_fn=visualize_navmesh, style=s_red)
                    self.getout_btn = ui.Button("Get Outline", clicked_fn=get_outline, style=s_red)
                    self.mke_out_btn = ui.Button("Make Outline", clicked_fn=make_outline, style=s_red)
                    self.bld_wall_btn = ui.Button("Build Walls", clicked_fn=make_walls, style=s_red)
                    self.make_wall_btn = ui.Button("Make Walls", clicked_fn=visualize_walls, style=s_red)

    def on_shutdown(self):
        print("[siborg.create.navmesh] siborg create navmesh shutdown")
