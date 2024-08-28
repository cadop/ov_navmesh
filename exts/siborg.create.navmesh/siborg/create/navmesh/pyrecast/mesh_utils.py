import shutil
import os
import tempfile

def decimate_mesh(obj_file, perc_dec=0.110017): 
    '''
    Decimate a mesh using pymeshlab.
    Returns the path to the decimated mesh.
    '''
    import pymeshlab

    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(obj_file)
    ms.meshing_decimation_clustering(threshold = pymeshlab.PercentageValue(perc_dec))
    temp_file = tempfile.NamedTemporaryFile(suffix=".obj", delete=False)
    ms.save_current_mesh(temp_file.name)
    temp_file.close()

    # get the path of the temporary obj file
    obj_file_path = temp_file.name 
    print(f'Temp file path: {obj_file_path}')

    # Copy the temporary obj file to a real file
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Create the relative path to the real file
    real_file_path = os.path.join(current_dir, 'decimated_mesh.obj')
    shutil.copy(obj_file_path, real_file_path)


    return temp_file.name
