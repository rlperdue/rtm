"""
Russell Perdue
2025/12/10
"""

from mpi4py import MPI
import numpy as np
from pathlib import Path
import re
import sys

# Arguments
dataset_ = Path(sys.argv[1])
auxgates = np.array([int(ag) for ag in sys.argv[2].split(',')])
vents = [int(vent) for vent in sys.argv[3].split(',')]

klist = np.load(dataset_ / 'klist.npy')
nsims = np.size(klist,0)
nregions = np.size(klist,1)

comm = MPI.COMM_WORLD
nprocesses = comm.Get_size()
processID = comm.Get_rank()
buffer = np.empty(1000,dtype='c')
nworkers = nprocesses - 1

for gate in auxgates:
    maxtimes = -1 * np.ones(nsims)
    process = -1 * np.ones(nsims, dtype=int)
    waiting = nsims + 0
    nsolved = 0
    
    while waiting > 0:
        for i in range(nworkers):
            if process[i] == -1 and nsolved < nsims:
                cmds = [f'LET nregions = {nregions}', 
                        f'LET gate = {gate}', 
                        f'LET vent = {vents[0]}']  # fix
                for j in range(nregions):
                    cmds.append(f'SCALEPERM "R{j+1}", {klist[nsolved,j]}')
                cmds.append('CALL Fill')
                for cmd in cmds:
                    line = (cmd+'\n').encode()
                    comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, tag=1)
                process[i] = nsolved + 1
                nsolved += 1
        for i in range(nworkers):
            if process[i] != -1:
                flag = comm.Iprobe(source=i+1, tag=1)
                if flag:
                    comm.Recv((buffer,len(buffer),MPI.CHARACTER), source=i+1, 
                              tag=1)
                    bufstr = bytes(buffer[:8]).decode('ascii')
                    maxtime = float(re.match(r'^\d+\.?\d*', bufstr).group())
                    ind = process[i] - 1
                    maxtimes[ind] = maxtime
                    waiting -= 1
                    process[i] = -1
    
    np.save(f'maxtimes{gate}', maxtimes)
    
for i in range(nworkers):
    comm.Send((b'EXIT\n',6,MPI.CHARACTER), dest=i+1, tag=1)
    