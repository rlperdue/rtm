"""
Russell Perdue
2025/12/10
"""

from mpi4py import MPI
import numpy as np
from pathlib import Path
import sys

# Arguments
dataset_ = Path(sys.argv[1])
aux = np.array([int(ag) for ag in sys.argv[2].split(',')])
vents = [int(vent) for vent in sys.argv[3].split(',')]

klist = np.load(dataset_ / 'klist.npy')
nsims = np.size(klist,0)
nregions = np.size(klist,1)
naux = np.size(aux)

datasetres = np.load('results.npz')
besttimes = datasetres['xbest']

comm = MPI.COMM_WORLD
nprocesses = comm.Get_size()
processID = comm.Get_rank()
buffer = np.empty(1000,dtype='c')
nworkers = nprocesses - 1

process = -1 * np.ones(nsims, dtype=int)
waiting = nsims + 0
nsolved = 0

while waiting > 0:
    for i in range(nworkers):
        if process[i] == -1 and nsolved < nsims:
            nsolved += 1
            process[i] = nsolved - 1
            cmds = [f'LET nregions = {nregions}', 
                    f'LET naux = {naux}', 
                    f'LET vent = {vents[0]}',  # fix
                    f'LET count = {process[i]}', 
                    'DIM k(nregions)', 
                    'DIM aux(naux)', 
                    'DIM taux(naux)']
            for j in range(nregions):
                cmds.append(f'LET k({j+1}) = {klist[process[i],j]}')
            taux_argsort = np.argsort(besttimes[process[i],:])
            aux_sort = aux[taux_argsort]
            taux_sort = besttimes[process[i],taux_argsort]
            for j in range(naux):
                cmds.append(f'LET aux({j+1}) = {aux_sort[j]}')
                cmds.append(f'LET taux({j+1}) = {taux_sort[j]}')
            cmds.append('CALL Fill')
            for cmd in cmds:
                line = (cmd+'\n').encode()
                comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, tag=1)
    for i in range(nworkers):
        if process[i] != -1:
            flag = comm.Iprobe(source=i+1, tag=1)
            if flag:
                comm.Recv((buffer,len(buffer),MPI.CHARACTER), source=i+1, 
                          tag=1)
                ind = process[i]
                waiting -= 1
                process[i] = -1
        
for i in range(nworkers):
    comm.Send((b'EXIT\n',6,MPI.CHARACTER), dest=i+1, tag=1)
    