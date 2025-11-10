"""
Russell Perdue
Created 2025/11/07
Last updated 2025/11/09
"""

from pathlib import Path
from rtm_rlperdue import setup, dataset, control_optim

class RTMEnv():
    def __init__(self):
        print('Welcome!')
        self.cwd = Path.cwd()
        self.menu0()
    
    def menu0(self):
        print('\nSelect option:')
        print('0   Create mesh.dmp from mesh.msh')
        print('1   Flatten mesh')
        print('2   Create dataset of uncontrolled flows')
        print('3   Optimize control action times')
        print('4   Optimize aux. gate locations')
        choice = input('>>> ')
        if choice=='0':
            self.menu1()
        elif choice=='1':
            self.menu2()
        elif choice=='2':
            self.menu3()
        elif choice=='3':
            self.menu4()
        elif choice=='4':
            self.menu4()
    
    def menu1(self):
        print('\nUpload mesh.msh: ')
        mesh_msh = Path(input('>>> '))
        self.remove_points(mesh_msh)
        mesh_dmp = setup.msh2dmp(mesh_msh)
        print(f'    {mesh_dmp.relative_to(self.cwd).as_posix()} saved.')
        self.menu0()
    
    def menu2(self):
        print('\nUpload mesh.msh: ')
        mesh_msh = Path(input('>>> '))
        self.remove_points(mesh_msh)
        mesh_obj = setup.msh2obj(mesh_msh)
        print(f'    {mesh_obj.relative_to(self.cwd).as_posix()} saved.')
        flat_obj = setup.flatten_mesh(mesh_obj)
        print(f'    {flat_obj.relative_to(self.cwd).as_posix()} saved.')
        self.menu0()
        
    def menu3(self):
        print('\nmenu3')
        
    def menu4(self):
        print('\nmenu4')
    
    def menu5(self):
        print('\nmenu5')
    
    def remove_points(self, mesh_msh):
        n_points_removed = setup.remove_points(mesh_msh)
        if n_points_removed > 0:
            print(f'    {n_points_removed} extraneous points removed.')
    

# %%
if __name__ == '__main__':
    env = RTMEnv()
