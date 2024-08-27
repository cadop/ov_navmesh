'''# python.exe .\setup.py build_ext --inplace'''


import shutil
import tempfile
from typing import List, Tuple, Dict, Any

import numpy as np

from . import PyRecast as rd
import os
from . import mesh_utils


class Navmesh:
    '''
    Python class to interface with navmesh.
    '''

    def __init__(self) -> None:
        ''' 
        Initializes a new instance of the NavmeshInterface class.
        '''
        self._navmesh = rd.NavmeshInterface()

    def load_obj(self, file_path: str) -> None:
        '''
        Load geometry from a *.obj file.

        Args:
            file_path (str): Path to the file with extension *.obj.
        '''
        self._navmesh.load_obj(file_path)
    def load_mesh(self, vertices: List[float], triangles: List[float]) -> None:
        '''
        Load mesh from vertices and triangles.

        Args:
            vertices (List[float]): List of vertices.
            triangles (List[float]): List of triangles.
        '''
        # It's not obvious how to pass vertices and triangles to the C++ code.
        # so instead we make a temporary obj file out of the data and secretly pass that

        # Create a temporary obj file in memory
        # vertices/=100

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.obj') as temp_file:
            obj_file_path = temp_file.name
            for vertex in vertices:
                temp_file.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
            for triangle in triangles:
                temp_file.write(f"f ")
                for tri in triangle:
                    temp_file.write(f"{tri+1} ")
                temp_file.write(f"\n")

        # get the path of the temporary obj file
        obj_file_path = temp_file.name 
        print(f'Temp file path: {obj_file_path}')

        # Copy the temporary obj file to a real file
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Create the relative path to the real file
        real_file_path = os.path.join(current_dir, 'file.obj')
        shutil.copy(obj_file_path, real_file_path)

        decimated_mesh = mesh_utils.decimate_mesh(obj_file_path)
        print(f'Decimated mesh path: {decimated_mesh}')

        self._navmesh.load_obj(decimated_mesh)
        # self._navmesh.load_obj(obj_file_path)

    def build_navmesh(self, settings: Dict[str, Any] = {}) -> None:
        '''
        Build the navmesh.

        Args:
            settings (Dict[str, Any]): A dictionary containing the settings for building the navmesh.
                The valid keys and their corresponding value types are:
                - "cellSize" (float): The size of a cell in the grid.
                - "cellHeight" (float): The height of a cell in the grid.
                - "agentHeight" (float): The height of the agent.
                - "agentRadius" (float): The radius of the agent.
                - "agentMaxClimb" (float): The maximum climb height of the agent.
                - "agentMaxSlope" (float): The maximum slope angle that the agent can traverse.
                - "regionMinSize" (int): The minimum size of a region.
                - "regionMergeSize" (int): The size threshold for merging regions.
                - "edgeMaxLen" (float): The maximum allowed length for an edge.
                - "edgeMaxError" (float): The maximum allowed error for an edge.
                - "vertsPerPoly" (float): The maximum number of vertices per polygon.
                - "detailSampleDist" (float): The distance between detail samples.
                - "detailSampleMaxError" (float): The maximum allowed error for detail samples.
                - "partitionType" (int): The partition type for the navmesh.

                Default settings will be used if a key is not provided in the settings dictionary.
        '''

        # Define the default settings in a dict
        default_settings = {
            "cellSize": 0.1,
            "cellHeight": 0.1,
            "agentHeight": 1.6,
            "agentRadius": 0.05,
            "agentMaxClimb": 0.2,
            "agentMaxSlope": 45.0,
            "regionMinSize": 0.5,
            "regionMergeSize": 20,
            "edgeMaxLen": 12.0,
            "edgeMaxError": 1.3,
            "vertsPerPoly": 6.0,
            "detailSampleDist": 6.0,
            "detailSampleMaxError": 1.0,
            "partitionType": 0
        }
        
        # Overriding the default settings with the user provided settings
        default_settings.update(settings)
    
        self._navmesh.build_navmesh(default_settings)

    def get_navmesh_raw_contours(self) -> Tuple[List[float], List[int], List[int]]:
        '''
        Get the raw contours of the navmesh.

        Returns:
            Tuple[List[float], List[int], List[int]]: A tuple containing the raw contours of the navmesh.
        '''
        return self._navmesh.get_navmesh_raw_contours()

    def get_navmesh_contours(self) -> Tuple[List[float], List[int], List[int]]:
        '''
        Get the contours of the navmesh.

        Returns:
            Tuple[List[float], List[int], List[int]]: A tuple containing the contours of the navmesh.
        '''
        return self._navmesh.get_navmesh_contours()
    
    def get_navmesh_triangles(self) -> List[float]:
        '''
        Get the triangles of the navmesh.

        Returns:
            List[float]: A list containing the triangles of the navmesh.
        '''
        return self._navmesh.get_navmesh_triangles()
    
    def get_navmesh_polygons(self) -> List[float]:
        '''
        Get the polygons of the navmesh.

        Returns:
            List[float]: A list containing the polygons of the navmesh.
        '''
        return self._navmesh.get_navmesh_polygons()
    
    def find_paths(self, starts, ends, searchSize=[10.0,10.0,10.0], pathMode=2, pathStyle=0) -> List[float]:
        '''
        Find paths between start and end points on the navmesh.

        Args:
            starts: The start points.
            ends: The end points.
            searchSize (List[float]): The search size.
            pathMode (int): The path mode.
            pathStyle (int): The path style.

        Returns:
            List[float]: A list containing the paths.
        '''
        starts = np.asarray(starts, dtype=np.float32).flatten()
        ends = np.asarray(ends, dtype=np.float32).flatten()

        return self._navmesh.find_paths(starts, ends, searchSize, pathMode, pathStyle)

    def find_paths_parallel(self, starts, ends, searchSize=[10.0,10.0,10.0], pathMode=2, pathStyle=0) -> List[float]:
        '''
        Find paths in parallel (uses openmp on the c++ side) between start and end points on the navmesh.

        Args:
            starts: The start points.
            ends: The end points.
            searchSize (List[float]): The search size.
            pathMode (int): The path mode.
            pathStyle (int): The path style.

        Returns:
            List[float]: A list containing the paths.
        '''
        starts = np.asarray(starts, dtype=np.float32).flatten()
        ends = np.asarray(ends, dtype=np.float32).flatten()

        return self._navmesh.find_paths_parallel(starts, ends, searchSize, pathMode, pathStyle)

    def get_random_points(self, num_points: int) -> List[float]:
        '''
        Return random points on the navmesh.

        Args:
            num_points (int): Number of random points to generate.

        Returns:
            List[float]: List of random points.
        '''
        res  = self._navmesh.get_random_points(num_points)
        res = np.asarray(res).reshape(-1,3)
        return res
    
