"""
Russell Perdue
Created 2025/11/09
Last updated 2025/11/09
"""

from pathlib import Path
import shutil

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
        return None
    
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
