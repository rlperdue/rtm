"""
Russell Perdue
Created 2025/11/09
Last updated 2025/11/13
"""

import itertools
import numpy as np
import os
from pathlib import Path
import subprocess
import tempfile

def make_lb(mesh_dmp: Path, regions_zon: Path, resfolder: Path) -> Path:
    nregions = 4
    scaleperm_strs = []
    for i in range(nregions):
        scaleperm_strs.append(f'SCALEPERM "R{i+1}", k({i+1})')
    scaleperm_block = '\n    '.join(scaleperm_strs)
    s = f'''
WARNINGS 0
DIM k(4)
DIM index
PROC Auto
    CHANGEDIR "{mesh_dmp.parent.resolve().as_posix()}"
    SETINTYPE "dmp"
    READ "{mesh_dmp.name}"
    CHANGEDIR "{regions_zon.parent.resolve().as_posix()}"
    REGLOAD "{regions_zon.name}", "*", 0
    SETTIME 0.0
    SETGATE "Gate", 1, 100000
    {scaleperm_block}
    DO WHILE SONUMBEREMPTY()>0
        SOLVE
    LOOP
    CHANGEDIR "{resfolder.resolve().as_posix()}"
    SETOUTTYPE "msh"
    WRITE "res"+STR(index)+".msh"
    PRINT 0
ENDPROC'''
    fp = tempfile.NamedTemporaryFile(mode='w+b', suffix='.lb', delete=False)
    fp.write(s.encode())
    fp.seek(0)
    worker_lb = Path(fp.name)
    return worker_lb
    
def make_dataset(kvalues: list[float], worker_lb: Path, resfolder: Path):
    if not os.path.exists(resfolder):
        os.mkdir(resfolder)
    os.mkdir(resfolder / 'out')
    
    nregions = 4
    klist = np.array([i for i in itertools.product(kvalues, repeat=nregions)])
    klist_npy = (resfolder / 'out/klist.npy').resolve().as_posix()
    np.save(klist_npy, klist)
    
    worker_lb = worker_lb.resolve().as_posix()
    
    cmds = ['@echo off', 
'call C:/Users/rperd/miniforge3/Scripts/activate.bat', 
'call cd C:/Users/rperd/OneDrive/Documents/GitHub/rtm/src/rtm_rlperdue/dataset_mpi.py', 
'call conda activate torch-env', 
f'call mpiexec -n 1 python dataset_mpi.py {klist_npy} : -n 7 mpilims -x -l{worker_lb}', 
'pause']
    cmd = ' && '.join(cmds)
    print(cmd)
    subprocess.run(cmd, shell=True)
    os.remove(worker_lb)
    
    
# %%
mesh_dmp = Path('../../tests/test1/bpillar.dmp')
regions_zon = Path('../../tests/test1/regions.zon')
resfolder = Path('../../tests/test1/dataset_mpi')
p = make_lb(mesh_dmp, regions_zon, resfolder)

