"""
Russell Perdue
2025/11/15
"""

from mpi4py import MPI
import numpy as np
import re
import sys

#def dataset_mpi(klist_npy: str):
def dataset_mpi():
    #klist = np.load(klist_npy)
    klist = np.load(r'C:/Users/rperd/OneDrive/Documents/GitHub/rtm/tests/test1/dataset0/out/klist.npy')
    nsims = np.size(klist,0)
    nregions = np.size(klist,1)
    
    comm = MPI.COMM_WORLD
    nprocesses = comm.Get_size()
    processID = comm.Get_rank()
    buffer = np.empty(1000,dtype='c')
    print(f'Started parent {processID}')
    
    nworkers = nprocesses - 1
    fill = -1 * np.ones(nsims)
    process = -1 * np.ones(nsims, dtype=int)
    waiting = nsims + 0
    unsolved = 0
    
    while waiting > 0:
        for i in range(nworkers):
            if process[i] == -1 and unsolved < nsims:
                for j in range(nregions):
                    line = f'LET k({j+1}) = {klist[unsolved,j]}\n'.encode()
                    comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, tag=1)
                line = f'LET index = {unsolved}\n'.encode()
                comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, tag=1)
                line = b'CALL Auto\n'
                comm.Send((line,len(line)+2,MPI.CHARACTER), dest=i+1, tag=1)
                process[i] = unsolved + 1
                unsolved += 1
                print(f'Dispatched {i+1} to solve {unsolved}')
        for i in range(nworkers):
            if process[i] != -1:
                flag = comm.Iprobe(source=i+1, tag=1)
                if flag:
                    comm.Recv((buffer,len(buffer),MPI.CHARACTER), source=i+1, tag=1)
                    bufstr = bytes(buffer[:16]).decode('ascii')
                    fill_ = re.match(r'^\d+\.?\d*', bufstr).group()
                    ind = process[i]
                    fill[ind-1] = fill_
                    waiting -= 1
                    process[i] = -1
                    print(f'{i+1} solved {ind} to be {fill_}')
    
    for i in range(nworkers):
        comm.Send((b'EXIT\n',6,MPI.CHARACTER), dest=i+1, tag=1)
    
    print('Shutting down master module...')

#dataset_mpi(sys.argv[1])
dataset_mpi()
