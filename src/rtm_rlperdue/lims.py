"""
Russell Perdue
2025/10/03
"""

from copy import deepcopy
import numpy as np
import os
import subprocess

class LimsToolbox:
    def __init__(self, template, lbfolder='lb_temp', resfolder='res_temp'):
        with open(template, 'r') as file:
            self.template_contents = file.read()
        
        for folder in [lbfolder, resfolder]:
            if folder is not None:
                if not os.path.exists(folder):
                    os.mkdir(folder)
        
        self.lbfolder = lbfolder
        self.resfolder = resfolder
        self.count = len(os.listdir(lbfolder))
    
    def new(self, **kwargs):
        newlb = f'{self.lbfolder}/lb{self.count}.lb'
        self.count += 1
        newlb_contents = deepcopy(self.template_contents)
        
        cwd = f'"{os.getcwd()}"'.replace('\\', '/')
        newlb_contents = newlb_contents.replace('[lbfolder]', cwd)
        if self.resfolder is not None:
            resfolder = f'"{os.path.abspath(self.resfolder)}"'
            resfolder = resfolder.replace('\\','/')
            newlb_contents = newlb_contents.replace('[resfolder]', resfolder)
        for name, val in kwargs.items():
            newlb_contents = newlb_contents.replace(f'[{name}]', f'{val}')
        
        with open(newlb, 'w') as file:
            file.write(newlb_contents)
        
        return os.path.abspath(newlb)
    
    def make_cmds(self, i=None):
        if isinstance(i, int):
            if i == -1:
                i = self.count - 1
            lb_abspath = os.path.abspath(f'{self.lbfolder}/lb{i}.lb')
            cmd = rf'C:\lhome\bin\lims.exe -l{lb_abspath}'
            return cmd
        
        cmds = []
        lbfiles = os.listdir(self.lbfolder)
        for file in lbfiles:
            lb_abspath = os.path.abspath(f'{self.lbfolder}/{file}')
            cmds.append(rf'C:\lhome\bin\lims.exe -l{lb_abspath}')
        return cmds
    
    def run(self, i=None):
        if isinstance(i, int):
            cmd = self.make_cmds(i)
            subprocess.call(cmd, stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        else:
            cmds = self.make_cmds()
            for cmd in cmds:
                subprocess.call(cmd, stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
    
    def extract_data(self, i=None):
        if isinstance(i, int):
            if i == -1:
                i = self.count - 1
            resfile = f'{self.resfolder}/res{i}.txt'
            while not os.path.exists(resfile):
                pass
            with open(resfile, 'r') as f:
                res = np.loadtxt(f)
            return res
        
        resfiles = os.listdir(self.resfolder)
        res = np.zeros(len(resfiles))
        for file in resfiles:
            with open(f'{self.resfolder}/{file}', 'r') as f:
                j = int(file.replace('res','').replace('.txt',''))
                res[j] = np.loadtxt(f)
        return res
