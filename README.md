# A Simple Navigation Mesh Extension based on Recast & Detour

<img width="1868" alt="image" src="https://github.com/user-attachments/assets/646c7cd1-30eb-439b-8131-4f0d9b285484" />

------------------

This extension is mostly designed for showing how to use the features of the navmesh interface.  

1. Create meshes in the scene (don't use, e.g. a 'capsule' prim).
2. Select the meshes you want included in the navmesh (ctrl+sel)
3. Click "Assign Mesh"
4. Click "Build Navmesh"

These are the main steps, you need to select the meshes to include, then assign those meshes.  After this, you can build the navmesh with the default or custom settings. 

To use custom settings, change the sliders in the dropdown and click "Save".  You can then press the "Build Navmesh" button again. 

If you want to see what the navmesh looks like, click on "Create Mesh"


To show how to call some of the useful features there are a few buttons:
- If you want to get random points on the navmesh, click "Get Random Points".  This will query random points on the navmesh and then display them.
The actual query is as follows, with an input param as the number of points to get:

`s,e = self.navmesh.get_random_points(2)`
<img width="853" alt="image" src="https://github.com/user-attachments/assets/057e3ecb-4e46-43e0-8f3e-3aea21f3e40e" />

- If you want to get a path, use either the button for a random path, or you can drag and drop a start and end prim into the text fields.
The query for a path is based on a start and end list.  If there are just one start and one end, it gives one path back, otherwise it will be a list of multiple paths (which is a list of points):

`path_pnts = self.navmesh.find_paths([s], [e])`
<img width="820" alt="image" src="https://github.com/user-attachments/assets/af1e151c-c51c-4cbc-b165-de2bd0f56659" />

- If you want to get a path between the two prims, the drag-drop into the text field will set them. Then click "Get start end path":
<img width="1157" alt="image" src="https://github.com/user-attachments/assets/f06ea055-6943-4948-bbe7-ee7c558158ae" />
 

The extension itself is just a demo, but it should help you get started with integrating the code in your own project. You will probably be best served by using the `Core.py` file, and its corresponding `pyrecast/__init__.py`.  
There are binaries for windows and linux, for Python 3.10 (which is the python version as of this release).
