import omni.ext
import omni.ui as ui
from pxr import Gf

from . import core
from . import usd_utils
from pxr import Usd, UsdGeom
import numpy as np

from omni.ui import color as cl

class SiborgCreateNavmeshExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[siborg.create.navmesh] siborg create navmesh startup")

        self._window = ui.Window("Navmesh", width=300, height=600)
        self.stage = omni.usd.get_context().get_stage()
        
        self.navmesh_settings = {}
        self.start_prim = None
        self.end_prim = None

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
                    self.pth_btn.style = s_red

                def assign_mesh():
                    # get the selected prim
                    # load the mesh
                    reset_btns()

                    stage = omni.usd.get_context().get_stage()
                    self.up_axis = UsdGeom.GetStageUpAxis(stage)
                    self.navmesh.z_up = self.up_axis == UsdGeom.Tokens.z

                    if self.navmesh.get_selected_prim():
                        self.assign_btn.style = s_done
                        self.bld_btn.style = s_yellow

                def build_navmesh():
                    # build the navmesh
                    self.navmesh.build_navmesh(settings=self.navmesh_settings)
                    self.bld_btn.style = s_done
                    self.rnd_pnts_btn.style = s_green
                    self.rnd_pth_btn.style = s_green
                    self.mesh_btn.style = s_yellow   
                    self.pth_btn.style = s_green 


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


                def get_specific_path():

                    # get sample path
                    if not self.start_prim or not self.end_prim:
                        print('No start or end prim')
                        return

                    time = Usd.TimeCode.Default() # The time at which we compute the bounding box
    
                    xform = UsdGeom.Xformable(self.start_prim)
                    s = xform.ComputeLocalToWorldTransform(time).ExtractTranslation()

                    xform = UsdGeom.Xformable(self.end_prim)
                    e = xform.ComputeLocalToWorldTransform(time).ExtractTranslation()

                    path_pnts = self.navmesh.find_paths([s], [e])
                    # plot the path
                    usd_utils.create_curve(path_pnts)


                def assign_start_prim(event):
                    item = event.mime_data
                    self.start_prim = item
                    self.startprim_field.model.set_value(item)
                    self.start_prim = self.stage.GetPrimAtPath(self.start_prim) 


                def assign_end_prim(event):
                    item = event.mime_data
                    self.end_prim = item
                    self.endprim_field.model.set_value(item)
                    self.end_prim = self.stage.GetPrimAtPath(self.end_prim) 

                with ui.VStack():
                    self.assign_btn = ui.Button("Assign Mesh", clicked_fn=assign_mesh, style=s_yellow)
                    self.bld_btn = ui.Button("Build Navmesh", clicked_fn=build_navmesh, style=s_red)
                    self.mesh_btn = ui.Button("Create Mesh", clicked_fn=visualize_navmesh, style=s_red)
                    self.rnd_pnts_btn = ui.Button("Get Random Points", clicked_fn=get_random_points, style=s_red)
                    self.rnd_pth_btn = ui.Button("Get Random Path", clicked_fn=get_path, style=s_red)
                    self.pth_btn = ui.Button("Get Start-End Path", clicked_fn=get_specific_path, style=s_red)


                with ui.HStack(height=30):
                    ui.Label("Start Prim")
                    self.startprim_field = ui.StringField(tooltip="Start")
                    self.startprim_field.set_accept_drop_fn(lambda item: True)
                    self.startprim_field.set_drop_fn(assign_start_prim)

                    ui.Label("End Prim")
                    self.endprim_field = ui.StringField(tooltip="End")
                    self.endprim_field.set_accept_drop_fn(lambda item: True)
                    self.endprim_field.set_drop_fn(assign_end_prim)


                def set_settings():

                    self.navmesh_settings['agentHeight'] = self.agent_height_float.get_value_as_float()
                    self.navmesh_settings['agentRadius'] = self.agent_radius_float.get_value_as_float()
                    self.navmesh_settings['agentMaxClimb'] = self.agent_step_float.get_value_as_float()
                    self.navmesh_settings['agentMaxSlope'] = self.agent_slope_float.get_value_as_float()

                def reset_settings():
                    self.navmesh_settings = {}    

                with ui.VStack():
                    with ui.CollapsableFrame("Navmesh Settings", collapsed=True):
                        with ui.VStack():
                            # Agent Height Slider
                            ui.Label("Agent Height")
                            self.agent_height_float = ui.SimpleFloatModel(2.0, min=0, max=100)
                            ui.FloatSlider(self.agent_height_float, width=200, min=0, max=100, step=0.01)
                            
                            # Agent Radius 
                            ui.Label("Agent Radius")
                            self.agent_radius_float  = ui.SimpleFloatModel(0.6, min=0,max=100)
                            ui.FloatSlider(self.agent_radius_float, width=200 ,min=0,max=100,step=0.01)

                            # Max Step 
                            ui.Label("Max Step")    
                            self.agent_step_float = ui.SimpleFloatModel(0.9, min=0,max=100)
                            ui.FloatSlider(self.agent_step_float, width=200 ,min=0,max=100,step=0.01)
                            
                            # Max Slope
                            ui.Label("Max Slope")    
                            self.agent_slope_float  = ui.SimpleFloatModel(45, min=0,max=89.9)
                            ui.FloatSlider(self.agent_slope_float , width=200 ,min=0,max=100,step=0.01)
                            

                    with ui.HStack():
                        ui.Button("Set Settings", clicked_fn=set_settings)
                        ui.Button("Reset Settings", clicked_fn=reset_settings)


    def on_shutdown(self):
        print("[siborg.create.navmesh] siborg create navmesh shutdown")
        self._window.destroy()
