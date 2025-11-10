"""
Russell Perdue
Created 2025/11/09
last updated 2025/11/09
"""

import meshio
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import NamedTemporaryFile

def msh2dmp(mesh_msh: Path) -> Path:
    LIMS_PATH = Path(r'C:\lhome\bin\lims.exe')
    
    mesh_msh = mesh_msh.resolve()
    mesh_dmp = mesh_msh.with_suffix('.dmp')
    
    # change back slashes to forward slashes
    mesh_msh = mesh_msh.as_posix()
    mesh_dmp = mesh_dmp.as_posix()
    
    # create temporary .lb file
    with NamedTemporaryFile(mode='w', suffix='.lb', delete=False) as fp:
        fp.write(f'READ "{mesh_msh}"')
        fp.write('\nSETOUTTYPE "dmp"')
        fp.write(f'\nWRITE "{mesh_dmp}"')
        fp.seek(0)
    
    # execute and remove .lb file
    cmd = f'{LIMS_PATH} -l{fp.name}'
    subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(fp.name)
    
    return Path(mesh_dmp)


def msh2obj(mesh_msh: Path) -> Path:
    mesh = meshio.read(mesh_msh)
    mesh_obj = mesh_msh.with_suffix('.obj')
    meshio.write(mesh_obj, mesh)
    return mesh_obj.resolve()


def flatten_mesh(mesh_obj: Path) -> Path:
    EXE_PATH = Path(r'C:\Users\rperd\OneDrive\Documents\GitHub\MeshParam\x64\Release\MeshParam.exe')
    flat_obj = mesh_obj.with_name(mesh_obj.stem + '_flat' + mesh_obj.suffix)
    cmd = ' '.join([str(EXE_PATH), str(mesh_obj), str(flat_obj)])
    subprocess.call(cmd)
    return flat_obj.resolve()


def remove_points(mesh_msh: Path) -> int:
    # read file
    with open(mesh_msh, 'r') as f:
        lines = [line.rstrip() for line in f]
    
    # count points to remove
    point0_ind = lines.index('$Elements') + 2
    n_points = 0
    i = point0_ind + 0
    while lines[i].split(' ')[1] == '15':  # 15 is a point element in Gmsh
        n_points += 1
        i += 1
    if n_points == 0:
        return 0
    
    # update number of elements
    n_elems = int(lines[point0_ind-1]) - n_points
    lines[point0_ind-1] = str(n_elems)
    
    # update element indices
    elem0_ind = point0_ind + n_points;
    for j in range(elem0_ind, elem0_ind+n_elems):
        line = lines[j].split(' ')
        line[0] = str(int(line[0]) - n_points)
        line = ' '.join(line)
        lines[j] = line
    
    # delete points
    del lines[point0_ind : elem0_ind]
    
    # create backup of original mesh file
    mesh_orig_msh = mesh_msh.with_name(mesh_msh.stem + '0' + mesh_msh.suffix)
    shutil.copy(mesh_msh, mesh_orig_msh)
    
    # overwrite original file
    with open(mesh_msh, 'w') as f:
        f.write(f'{lines[0]}')
        for line in lines[1:]:
            f.write(f'\n{line}')
    
    return n_points
