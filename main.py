"""
Russell Perdue
Created 2025/11/07
Last updated 2025/11/09
"""

from pathlib import Path
from rtm_optim import (remove_points, 
                       msh2dmp, 
                       msh2obj, 
                       flatten_mesh, 
                       #loc_optim, 
                       #control_optim, 
                       )

def main():
    '''
    print('Upload mesh:')
    mesh_msh = Path(input('>>> '))'''
    mesh_msh = Path('test1/bpillar.msh')
    
    n_points = remove_points(mesh_msh)
    if n_points > 0:
        print(f'Removed {n_points} extraneous points.')
    
    mesh_dmp = msh2dmp(mesh_msh)
    print('Created .dmp file.')
    
    mesh_obj = msh2obj(mesh_msh)
    print('Created .obj file.')
    
    '''
    nodes_uv = flatten_mesh(mesh_obj)
    print('Flattened mesh.')
    
    print('Upload regions:')
    regions = input('>>> ')
    
    print('Number of aux. gates:')
    n_auxgates = input('>>> ')
    
    print('Press ENTER to begin aux. gate location optimization process')
    input('>>> ')
    auxgate_nodes = loc_optim(mesh_dmp, regions, nodes_uv, n_auxgates)
    for i, node in enumerate(auxgate_nodes):
        print(f'Aux gate {i+1}: {node}')
    
    print('Press ENTER to begin control action time optimization process')
    input('>>> ')
    control_optim(mesh_dmp, regions, nodes_uv, auxgate_nodes)'''
    
    
# %%
if __name__ == '__main__':
    main()
