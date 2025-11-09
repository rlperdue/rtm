"""
Russell Perdue
Created 2025/11/07
Last updated 2025/11/07
"""

from rtm_optim import (dmp2msh, 
                       remove_points, 
                       msh2obj, 
                       flatten_mesh, 
                       loc_optim, 
                       control_optim, 
                       )

def main():
    print('Upload mesh')
    mesh_dmp = input('>>> ')
    
    print('Converting to msh...')
    mesh_msh = dmp2msh(mesh_dmp)
    
    print('Removing extraneous points...')
    remove_points(mesh_msh)
    
    print('Converting to obj...')
    mesh_obj = msh2obj(mesh_msh)
    
    print('Flattening...')
    nodes_uv = flatten_mesh(mesh_obj)
    
    print('Upload regions')
    regions = input('>>> ')
    
    print('Number of aux. gates?')
    n_auxgates = input('>>> ')
    
    print('Press ENTER to begin aux. gate location optimization process')
    input('>>> ')
    auxgate_nodes = loc_optim(mesh_dmp, regions, nodes_uv, n_auxgates)
    for i, node in enumerate(auxgate_nodes):
        print(f'Aux gate {i+1}: {node}')
    
    print('Press ENTER to begin control action time optimization process')
    input('>>> ')
    control_optim(mesh_dmp, regions, nodes_uv, auxgate_nodes)
    

if __name__ == '__main__':
    main()
