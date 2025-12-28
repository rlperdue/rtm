"""
Russell Perdue
2025/11/25
"""

import os
from pathlib import Path
from rtm_rlperdue import rtm
import subprocess
import sys
import tkinter as tk
from tkinter.filedialog import askdirectory
from typing import Tuple
import zipfile

class CLI():
    def __init__(self):
        print('Welcome!')
        self.rtm_ = Path.cwd()
        self.config = self.get_config(self.rtm_)

        self.command_line_mode = False
        if len(sys.argv[1:]) > 0:
            self.command_line_mode = True
        
        self.menu0()
            
    def menu0(self):
        print('Run local (0) or remote (1)?')
        if not self.command_line_mode:
            self.remote = int(input('>>> '))
        else:
            self.remote = 0
        print('OK')

        if self.command_line_mode:
            self.test_ = Path(self.rtm_/'tests'/sys.argv[1]).resolve()
            os.chdir(self.test_)
        else:
            print('Select test folder:')
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            initialdir = self.rtm_ / 'tests'
            self.test_ = Path(askdirectory(initialdir=initialdir)).resolve()
            os.chdir(self.test_)
            print('Done')
        
        if not os.path.exists('mesh'):
            sys.exit('"mesh/" not found')
        for file in ['mesh.dmp', 'mesh.msh', 'regions.zon']:
            if not os.path.exists(f'mesh/{file}'):
                sys.exit(f'"mesh/{file}" not found')
        
        self.meshdata = self.get_meshdata()
        
        self.menu1()
        
    def menu1(self):
        print('Select option:')
        print('0   Flatten mesh')
        print('1   Create dataset')
        print('2   Optimize control action times')
        print('3   Optimize aux. gate locations')
        print('4   Quit')
        if self.command_line_mode:
            choice = int(sys.argv[2])
        else:
            choice = int(input('>>> '))
        
        if choice == 0:
            print('Flattening mesh...')
            state = rtm.flatten(self.test_)
            if state == 0:
                print('Done')
        elif choice == 1:
            if self.command_line_mode:
                kvalues_raw = sys.argv[3]
            else:
                print('List racetracking strengths separated by commas:')
                kvalues_raw = input('>>> ')
            kvalues = [float(val) for val in kvalues_raw.split(',')]
            print('Creating dataset...')
            if self.remote:
                args = [str(self.test_.relative_to(self.rtm_/'tests')), 
                        '1', 
                        kvalues_raw
                ]
                state = self.execute_remote(args)
            else:
                state = rtm.dataset(self.test_, kvalues, self.meshdata, 
                                    self.config)
            if state == 0:
                print('Done')
        elif choice == 2:
            if self.command_line_mode:
                dataset_ = Path(self.test_/sys.argv[3])
                auxgates = sys.argv[4]
                name = sys.argv[5]
            else:
                print('Select dataset:')
                root = tk.Tk()
                root.withdraw()
                root.wm_attributes('-topmost', 1)
                dataset_ = Path(tk.filedialog.askdirectory(initialdir=self.test_))
                print('List aux. gate nodes separated by commas:')
                auxgates = input('>>> ')
                print('Enter folder name:')
                name = input('>>> ')
            print('Optimizing control action times...')
            if self.remote:
                args = [str(self.test_.relative_to(self.rtm_/'tests')), 
                        '2', 
                        str(dataset_), 
                        auxgates, 
                        name
                ]
                state = self.execute_remote(args)
            else:
                state = rtm.control(dataset_, auxgates, name, self.meshdata, 
                                    self.config)
            if state == 0:
                print('Done')
        elif choice == 3:
            if self.command_line_mode:
                dataset_ = Path(self.test_/sys.argv[3])
                naux = int(sys.argv[4])
                name = sys.argv[5]
            else:
                print('Select dataset:')
                root = tk.Tk()
                root.withdraw()
                root.wm_attributes('-topmost', 1)
                dataset_ = Path(tk.filedialog.askdirectory(initialdir=self.test_))
                print('Enter number of aux. gates:')
                naux = int(input('>>> '))
                print('Enter folder name:')
                name = input('>>> ')
            print('Optimizing aux. gate locations...')
            if self.remote:
                args = [str(self.test_.relative_to(self.rtm_/'tests')), 
                        '3', 
                        str(dataset_), 
                        str(naux), 
                        name,
                ]
                state = self.execute_remote(args)
            else:
                state = rtm.location(dataset_, naux, name, self.meshdata, 
                                    self.config)
            if state == 0:
                print('Done')
        elif choice == 4:
            print('Goodbye!')
            sys.exit()
        
        if not self.command_line_mode:
            self.menu1()
    
    def execute_remote(self, args):
        testfolder = args[0]
        task = args[1]
        zippath = Path('to_server.zip').resolve()
        os.chdir(self.rtm_)
        with zipfile.ZipFile(zippath, 'w') as zipf:
            zipf.write(f'tests/{testfolder}/mesh')
            for file in os.listdir(f'tests/{testfolder}/mesh'):
                zipf.write(f'tests/{testfolder}/mesh/{file}')
            if task == 2 or task == 3:
                dataset = args[2]
                zipf.write(f'tests/{testfolder}/{dataset}')
                for file in os.listdir(f'tests/{testfolder}/{dataset}'):
                    zipf.write(f'tests/{testfolder}/{dataset}/{file}')
        os.chdir(self.test_)
        subprocess.call(f'scp {zippath} server:/Users/rperd/Desktop/rtm')

        miniforge_ = self.config[2]
        env_ = self.config[3]
        cmds = ' && '.join([
            'cd Desktop/rtm', 
            'powershell -Command Expand-Archive to_server.zip -DestinationPath .', 
            'del to_server.zip', 
            'git pull', 
            f'{miniforge_}', 
            f'conda activate {env_}', 
            f'python main.py {' '.join(args)}'
        ])
        subprocess.run(f'ssh -o BatchMode=yes server {cmds}')
        os.remove(zippath)

        return 0

    def get_meshdata(self):
        with open('mesh/mesh.msh', 'r') as file:
            # nodes
            lines = file.readlines()
            nnodes = int(lines[4].strip())
        with open('mesh/regions.zon', 'r') as file:
            # regions
            lines = file.readlines()
            nregions = sum([line.startswith('R') for line in lines])
            # gates
            gate_ind = lines.index('Gate\n')
            R1_ind = lines.index('R1\n')
            gates = []
            for i in range(gate_ind+3,R1_ind):
                if lines[i].strip() == '':
                    continue
                gates_i = [int(gate) for gate in lines[i].strip().split(' ')]
                gates.extend(gates_i)
            # vents
            vent_ind = lines.index('Vent\n')
            vents = []
            for i in range(vent_ind+3,len(lines)):
                if lines[i].strip() == '':
                    continue
                vents_i = [int(vent) for vent in lines[i].strip().split(' ')]
                vents.extend(vents_i)
        with open('mesh/sensors.txt', 'r') as file:
            lines = file.readlines()
            sensors = [int(line) for line in lines]
        return (nnodes, nregions, gates, vents, sensors)
    
    def get_config(self, rtm_: Path) -> Tuple[Path]:
        with open(rtm_/'config.txt', 'r') as file:
            lines = file.readlines()        
        lims_ = Path(lines[lines.index('lims\n')+1].strip())
        mpilims_ = Path(lines[lines.index('mpilims\n')+1].strip())
        miniforge_ = Path(lines[lines.index('miniforge\n')+1].strip())
        env_ = Path(lines[lines.index('environment\n')+1].strip())
        return (lims_, mpilims_, miniforge_, env_)
        
if __name__ == '__main__':
    CLI()
