"""
Russell Perdue
2025/11/30
"""

import matplotlib.pyplot as plt
from mpi4py import MPI
import numpy as np
from pathlib import Path
import re
from skopt import Optimizer
from skopt.learning import GaussianProcessRegressor
import sys

# Arguments
dataset_ = Path(sys.argv[1])
aux = np.array([int(ag) for ag in sys.argv[2].split(',')])
vents = [int(vent) for vent in sys.argv[3].split(',')]

klist = np.load(dataset_/'klist.npy')
sensortime = np.load(dataset_/'sensortimes.npy')
#maxtimes_main = np.load(dataset_/'maxtimes.npy')
maxtime = np.load(dataset_/'maxtimes.npy')
nscenarios = np.size(klist,0)
nregions = np.size(klist,1)
naux = np.size(aux)
'''
maxtimes_all = np.zeros((nscenarios,naux+1))
maxtimes_all[:,0] = maxtimes_main
for i in range(naux):
    maxtimes_all[:,i+1] = np.load(f'maxtimes{aux[i]}.npy')
maxtime = np.max(maxtimes_all, axis=1)'''

comm = MPI.COMM_WORLD
nprocesses = comm.Get_size()
processID = comm.Get_rank()
buffer = np.empty(256,dtype='c')

nworkers = nprocesses - 1
process = -1 * np.ones(nworkers, dtype=int)
nstarted = 0
nsolved = 0

optimizer = [None] * nworkers
taux = [-1] * nworkers
ready = np.ones(nworkers, dtype=int)

max_calls = 10
n_initial_points = 1
times = -1 * np.ones((nscenarios, max_calls, naux))
fills = -1 * np.ones((nscenarios, max_calls))
iters = np.zeros(nscenarios, dtype=int)

while nsolved < nscenarios:
    for i in range(nworkers):
        if ready[i]:
            if process[i] == -1 and nstarted < nscenarios:
                process[i] = nstarted
                nstarted += 1
                #bounds = (sensortime[process[i]], maxtime[process[i]])
                bounds = (0, maxtime[process[i]])
                optimizer[i] = Optimizer(
                    [bounds for _ in range(naux)],
                    base_estimator=GaussianProcessRegressor(), 
                    n_initial_points=n_initial_points, 
                    initial_point_generator='random',  
                    )
            ready[i] = 0
            taux[i] = np.array(optimizer[i].ask())
            taux_sort = np.sort(taux[i])
            taux_argsort = np.argsort(taux[i])
            aux_sort = aux[taux_argsort]
            cmds = [f'LET nregions = {nregions}', 
                    f'LET naux = {naux}', 
                    f'LET vent = {vents[0]}',  # fix
                    'DIM k(nregions)', 
                    'DIM aux(naux)', 
                    'DIM taux(naux)']
            for j in range(nregions):
                cmds.append(f'LET k({j+1}) = {klist[process[i],j]}')
            for j in range(naux):
                cmds.append(f'LET aux({j+1}) = {aux_sort[j]}')
                cmds.append(f'LET taux({j+1}) = {taux_sort[j]}')
            cmds.append('CALL Fill')
            for cmd in cmds:
                line = (cmd+'\n').encode()
                comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, 
                    tag=1)
    for i in range(nworkers):
        if process[i] != -1:
            flag = comm.Iprobe(source=i+1, tag=1)
            if flag:
                comm.Recv((buffer,255,MPI.CHARACTER), source=i+1, 
                          tag=1)
                bufstr = bytes(buffer[:8]).decode('ascii')
                fill = float(re.match(r'^\d+\.?\d*', bufstr).group())
                ready[i] = 1
                ind = process[i]
                times[ind, iters[ind], :] = taux[i]
                fills[ind, iters[ind]] = fill
                iters[ind] += 1
                if iters[ind] == max_calls or fill > 0.99:
                    process[i] = -1
                    nsolved += 1
                else:
                    cost = -1 * fill
                    optimizer[i].tell(taux[i].tolist(), cost)

for i in range(nworkers):
    comm.Send((b'EXIT\n',6,MPI.CHARACTER), dest=i+1, tag=1)

nft = np.load(dataset_/'nodalfilltimes.npy')
nnodes = np.size(nft,0)
for i in range(nscenarios):
    cummax_i = [np.max(fills[i,:j+1]) for j in range(max_calls)]
    for j in range(max_calls):
        if fills[i,j] == -1:
            cummax_i[j] = -1
    uncontrolledfill = 1 - np.sum(nft[:,i] > nft[vents[0]-1,i]) / nnodes
    plt.figure()
    plt.plot(range(max_calls), cummax_i, '.')
    plt.plot(range(max_calls), uncontrolledfill*np.ones(max_calls))
    plt.ylim([0,1.1])
    plt.savefig(f'convergence_plots/convergence{i}.png')
    plt.close()

bestinds = np.argmax(fills, axis=1)
#bestfills = fills[:,bestinds]
besttimes = np.zeros((nscenarios,naux))
bestfills = np.zeros(nscenarios)
for i in range(nscenarios):
    besttimes[i,:] = times[i,bestinds[i],:]
    bestfills[i] = np.max(fills[i,:])

np.savez('results.npz', 
         x=times, 
         y=fills, 
         iters=iters,
         xbest=besttimes,
         ybest=bestfills)
