import numpy as np
from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, Vt
import omni


def traverse_instanced_children(prim):
    """Get every Prim child beneath `prim`, even if `prim` is instanced.

    Important:
        If `prim` is instanced, any child that this function yields will
        be an instance proxy.

    Args:
        prim (`pxr.Usd.Prim`): Some Prim to check for children.

    Yields:
        `pxr.Usd.Prim`: The children of `prim`.

    """
    for child in prim.GetFilteredChildren(Usd.TraverseInstanceProxies()):
        yield child

        for subchild in traverse_instanced_children(child):
            yield subchild

def parent_and_children_as_mesh(parent_prim):
    if parent_prim.IsA(UsdGeom.Mesh):
        points, faces = get_mesh(parent_prim)
        return points, faces
    
    found_meshes = []
    for x in traverse_instanced_children(parent_prim):
        if x.IsA(UsdGeom.Mesh):
            found_meshes.append(x)

    # children = parent_prim.GetAllChildren()
    # children = [child.GetPrimPath() for child in children]
    # points, faces = get_mesh(children)
    points, faces = get_mesh(found_meshes)
    
    return points, faces

def children_as_mesh(stage, parent_prim):
    children = parent_prim.GetAllChildren()
    children = [child.GetPrimPath() for child in children]
    points, faces = get_mesh(stage, children)
    
    return points, faces

def get_all_stage_mesh(stage):

    found_meshes = []

    # Traverse the scene graph and print the paths of prims, including instance proxies
    for x in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()):
        if x.IsA(UsdGeom.Mesh):
            found_meshes.append(x)

    points, faces = get_mesh(found_meshes)
   
    return points, faces

def get_mesh(obj):

    points, faces = [],[]

    f_offset = len(points)
    f, p = meshconvert(obj)
    # if len(p) == 0: continue
    points.extend(p)
    faces.extend(f+f_offset)

    return points, faces

def meshconvert(prim):

    # Create an XformCache object to efficiently compute world transforms
    xform_cache = UsdGeom.XformCache()

    # Get the mesh schema
    mesh = UsdGeom.Mesh(prim)
    
    # Get verts and triangles
    tris = mesh.GetFaceVertexIndicesAttr().Get()
    if not tris:
        return [], []
    tris_cnt = mesh.GetFaceVertexCountsAttr().Get()

    # Get the vertices in local space
    points_attr = mesh.GetPointsAttr()
    local_points = points_attr.Get()
    
    # Convert the VtVec3fArray to a NumPy array
    points_np = np.array(local_points, dtype=np.float64)
    
    # Add a fourth component (with value 1.0) to make the points homogeneous
    num_points = len(local_points)
    ones = np.ones((num_points, 1), dtype=np.float64)
    points_np = np.hstack((points_np, ones))

    # Compute the world transform for this prim
    world_transform = xform_cache.GetLocalToWorldTransform(prim)

    # Convert the GfMatrix to a NumPy array
    matrix_np = np.array(world_transform, dtype=np.float64).reshape((4, 4))

    # Transform all vertices to world space using matrix multiplication
    world_points = np.dot(points_np, matrix_np)

    tri_list = convert_to_triangle_mesh(tris, tris_cnt)
    # tri_list = tri_list.flatten()

    world_points = world_points[:,:3]

    return tri_list, world_points

def convert_to_triangle_mesh(FaceVertexIndices, FaceVertexCounts):
    """
    Convert a list of vertices and a list of faces into a triangle mesh.
    
    A list of triangle faces, where each face is a list of indices of the vertices that form the face.
    """
    
    # Parse the face vertex indices into individual face lists based on the face vertex counts.

    faces = []
    start = 0
    for count in FaceVertexCounts:
        end = start + count
        face = FaceVertexIndices[start:end]
        faces.append(face)
        start = end

    # Convert all faces to triangles
    triangle_faces = []
    for face in faces:
        if len(face) < 3:
            newface = []  # Invalid face
        elif len(face) == 3:
            newface = [face]  # Already a triangle
        else:
            # Fan triangulation: pick the first vertex and connect it to all other vertices
            v0 = face[0]
            newface = [[v0, face[i], face[i + 1]] for i in range(1, len(face) - 1)]

        triangle_faces.extend(newface)
    
    return np.array(triangle_faces)


def create_geompoints(boid_positions):
    '''create and manage geompoints representing agents

    Parameters
    ----------
    stage_path : str, optional
        if not set, will use /World/Points, by default None
    color : (r,g,b), optional
        if not set, will make color red, by default None
    '''
    
    stage_loc = "/World/Points"

    stage = omni.usd.get_context().get_stage()
    agent_point_prim = UsdGeom.Points.Define(stage, stage_loc)
    agent_point_prim.CreatePointsAttr()

    agent_point_prim.CreateDisplayColorAttr()
    # For RTX renderers, this only works for UsdGeom.Tokens.constant
    color_primvar = agent_point_prim.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant)
    
    point_color = (1, 0, 0)
    color_primvar.Set([point_color])
    
    boid_positions = Vt.Vec3fArray.FromNumpy(np.asarray(boid_positions, dtype=float))

    set_positions(agent_point_prim, boid_positions)


def set_positions(agent_point_prim, positions):
    
    agent_point_prim.GetPointsAttr().Set(positions)


def create_curve(nodes, prim_path="/World/Path"):
    '''Create and draw a BasisCurve on the stage following the nodes'''

    stage = omni.usd.get_context().get_stage()
    prim = UsdGeom.BasisCurves.Define(stage, prim_path)
    prim.CreatePointsAttr(nodes)

    # Set the number of curve verts to be the same as the number of points we have
    curve_verts = prim.CreateCurveVertexCountsAttr()
    curve_verts.Set([len(nodes)])

    # Set the curve type to linear so that each node is connected to the next
    type_attr = prim.CreateTypeAttr()
    type_attr.Set('linear')
    type_attr = prim.GetTypeAttr().Get()
    # Set the width of the curve
    # width_attr = prim.CreateWidthsAttr()
    # # width_attr = prim.CreateWidthsAttr(UsdGeom.Tokens.varying)
    # width_attr.Set(np.array([1.0], dtype=float))

    # color_primvar = prim.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant)
    UsdGeom.Primvar(prim.GetDisplayColorAttr()).SetInterpolation("constant")
    prim.GetDisplayColorAttr().Set([(0, 1, 0)])



def create_mesh(prim_path, points, indices, colors=None, opacity=None, use_prevsrf=True):
    '''
    Create a mesh in USD
    '''

    time = Usd.TimeCode.Default()
    stage = omni.usd.get_context().get_stage()

    mesh = UsdGeom.Mesh.Define(stage, prim_path)
    mesh.GetPointsAttr().Set(points, time)
    mesh.GetFaceVertexIndicesAttr().Set(indices, time)
    mesh.GetFaceVertexCountsAttr().Set([3] * len(indices), time)

    if use_prevsrf:

        mtl_path = Sdf.Path(f"/World/Looks/PreviewSurface_{prim_path.split('/')[-1]}")

        mtl = UsdShade.Material.Define(stage, mtl_path)
        shader = UsdShade.Shader.Define(stage, mtl_path.AppendPath("Shader"))
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(colors) 
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.0)
        mtl.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
            
        # Bind the mesh
        UsdShade.MaterialBindingAPI(mesh).Bind(mtl)

    # Opacity seems to be broken
    else:
        UsdGeom.Primvar(mesh.GetDisplayColorAttr()).SetInterpolation("constant")
        UsdGeom.Primvar(mesh.GetDisplayOpacityAttr()).SetInterpolation("constant")
        if colors:
            mesh.GetDisplayColorAttr().Set(colors, time)
        if opacity:
            mesh.GetDisplayOpacityAttr().Set(opacity, time)

    return prim_path

