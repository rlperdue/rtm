"""
Russell Perdue
2025/11/29
"""

from mpi4py import MPI
import numpy as np
import os
import sys

klist_npy = sys.argv[1]
klist = np.load(klist_npy)
nsims = np.size(klist,0)
nregions = np.size(klist,1)

comm = MPI.COMM_WORLD
nprocesses = comm.Get_size()
processID = comm.Get_rank()
buffer = np.empty(1000,dtype='c')
print(f'Started parent {processID}')

nworkers = nprocesses - 1
fills = -1 * np.ones(nsims)
process = -1 * np.ones(nsims, dtype=int)
waiting = nsims + 0
nsolved = 0

while waiting > 0:
    for i in range(nworkers):
        if process[i] == -1 and nsolved < nsims:
            cmds = [f'LET count = {nsolved}', 
                    f'LET nregions = {nregions}', 
                    'DIM k(nregions)']
            for j in range(nregions):
                cmds.append(f'LET k({j+1}) = {klist[nsolved,j]}')
            cmds.append('CALL Fill')
            for cmd in cmds:
                line = (cmd+'\n').encode()
                comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, tag=1)
            process[i] = nsolved + 1
            nsolved += 1
            print(f'Dispatched {i+1} to solve {nsolved}')
    for i in range(nworkers):
        if process[i] != -1:
            flag = comm.Iprobe(source=i+1, tag=1)
            if flag:
                comm.Recv((buffer,len(buffer),MPI.CHARACTER), source=i+1, 
                          tag=1)
                ind = process[i]
                waiting -= 1
                process[i] = -1
                print(f'{i+1} solved {ind}')

for i in range(nworkers):
    comm.Send((b'EXIT\n',6,MPI.CHARACTER), dest=i+1, tag=1)

print('Shutting down master module...')
