"""
Russell Perdue
2025/11/25
"""

import itertools
import matplotlib.pyplot as plt
import meshio
import numpy as np
import os
from pathlib import Path
import shutil
from skopt import Optimizer
from skopt.learning import GaussianProcessRegressor
import subprocess
from tqdm import tqdm

def flatten(test_: Path):
    # convert to obj
    mesh_msh = test_ / 'mesh/mesh.msh'
    mesh = meshio.read(mesh_msh)
    mesh_obj = mesh_msh.with_suffix('.obj').resolve()
    meshio.write(mesh_obj, mesh)
    
    # flatten mesh
    flatten_exe = test_ / '../../src/rtm_rlperdue/geogram/flatten.exe'
    flatten_exe = flatten_exe.resolve()
    flatmesh_obj = (test_ / 'mesh/mesh_flat.obj').resolve()
    cmd = ' '.join([str(flatten_exe), str(mesh_obj), str(flatmesh_obj)])
    subprocess.call(cmd)
    
    # save node coordinates of flattened mesh
    pos = []
    with open(flatmesh_obj) as file:
        for line in file:
            if line[:2] == 'vt':
                line = line.split(' ')
                pos.append(np.float32([line[1], line[2]]))
    pos = np.array(pos)
    np.save(test_/'mesh/mesh_flat.npy', pos)
    
    # save graph of flattened mesh
    plt.figure()
    plt.scatter(pos[:,0], pos[:,1])
    plt.savefig(test_/'mesh/mesh_flat.png')
    
    return 0


def dataset(test_: Path, kvalues: list[float], meshdata, config):
    # make folder
    kvaluestr = '_'.join([str(int(k)) for k in kvalues])
    dataset_ = test_/f'dataset_{kvaluestr}'
    os.mkdir(dataset_)
    res_ = dataset_/'res'
    os.mkdir(res_)
    
    # make klist
    nnodes, nregions, _, vents, sensors = meshdata
    klist = np.array([i for i in itertools.product(kvalues, repeat=nregions)])
    nsims = np.size(klist,0)
    klist_npy = Path(dataset_/'klist.npy').resolve()
    np.save(klist_npy, klist)
    
    # make dataset
    _, mpilims_, miniforge_, env_ = config
    rtm_rlperdue_ = Path(test_/'../../src/rtm_rlperdue').resolve()
    dataset_m_py = Path(rtm_rlperdue_ / 'masters/dataset_m.py')
    dataset_w_lb = Path(rtm_rlperdue_ / 'workers/dataset_w.lb')
    klist_npy = klist_npy.relative_to(dataset_)
    terminal_cmds = [
        '@echo off', 
        f'call {miniforge_}', 
        f'call conda activate {env_}', 
        f'call cd {dataset_}', 
        f'call mpiexec -n 1 python {dataset_m_py} {klist_npy} : '\
        f'-n 7 {mpilims_} -x -l{dataset_w_lb}']
    subprocess.call(' && '.join(terminal_cmds), shell=True)
    
    # nodal fill time data
    nodalfilltimes = np.zeros((nnodes,nsims))
    resfiles = os.listdir(res_)
    with open(res_/resfiles[0], 'r') as file:
        lines = file.readlines()
        endelements_ind = lines.index('$EndElements\n')
        skip_header = endelements_ind + 9 + 1
    for file in resfiles:
        i = int(file.replace('res','').replace('.msh',''))
        nodalfilltimes[:,i] = np.genfromtxt(res_/file, 
                                            skip_header=skip_header, 
                                            usecols=1, 
                                            max_rows=nnodes)
    np.save(dataset_/'nodalfilltimes.npy', nodalfilltimes)
    
    # max simulation times
    maxtimes = np.zeros(nsims)
    ventinds = np.array(vents) - 1
    for i in range(nsims):
        maxtimes[i] = np.min(nodalfilltimes[ventinds,i])
    np.save(dataset_/'maxtimes.npy', maxtimes)
    
    # penultimate sensor arrival times
    sensortimes = np.zeros(nsims)
    for i in range(nsims):
        sensortimes_i = nodalfilltimes[sensors,i]
        sensortimes[i] = np.sort(sensortimes_i)[-2]
    np.save(dataset_/'sensortimes.npy', sensortimes)
    
    return 0


def control(dataset_: Path, auxgates: str, name: str, meshdata, config, 
            location_optim=False):
    _, _, _, vents, _ = meshdata
    _, mpilims_, miniforge_, env_ = config
    
    # make folder
    control_ = Path(name).resolve()
    os.mkdir(control_)
    os.mkdir(control_/'convergence_plots')
    os.mkdir(control_/'res')
    '''
    # get max. fill time data for each aux. gate
    rtm_rlperdue_ = Path(dataset_/'../../../src/rtm_rlperdue').resolve()
    maxtimes_m_py = Path(rtm_rlperdue_ / 'masters/maxtimes_m.py')
    maxtimes_w_lb = Path(rtm_rlperdue_ / 'workers/maxtimes_w.lb')
    ventstr = ','.join([str(vent) for vent in vents])
    cmds_maxtime = [
        '@echo off', 
        f'call {miniforge_}', 
        f'call conda activate {env_}', 
        f'call cd {control_}', 
        f'call mpiexec -n 1 python {maxtimes_m_py} {dataset_} {auxgates} '\
            f'{ventstr} : -n 7 {mpilims_} -x -l{maxtimes_w_lb}']
    subprocess.call(' && '.join(cmds_maxtime), shell=True)'''
    
    # optimize control action times
    rtm_rlperdue_ = Path(dataset_/'../../../src/rtm_rlperdue').resolve()
    control_m_py = Path(rtm_rlperdue_ / 'masters/control_m.py')
    if location_optim:
        control_w_lb = Path(rtm_rlperdue_ / 'workers/control-LO_w.lb')
    else:
        control_w_lb = Path(rtm_rlperdue_ / 'workers/control_w.lb')
    ventstr = ','.join([str(vent) for vent in vents])
    cmds_control = [
        '@echo off', 
        f'call {miniforge_}', 
        f'call conda activate {env_}', 
        f'call cd {control_}', 
        f'call mpiexec -n 1 python {control_m_py} {dataset_} {auxgates} '\
            f'{ventstr} : -n 7 {mpilims_} -x -l{control_w_lb}']
    subprocess.call(' && '.join(cmds_control), shell=True)
    
    # save a msh file of the controlled fill for each scenario
    if not location_optim:
        test_m_py = Path(rtm_rlperdue_ / 'masters/test_m.py')
        test_w_lb = Path(rtm_rlperdue_ / 'workers/test_w.lb')
        cmds_test = [
            '@echo off', 
            f'call {miniforge_}', 
            f'call conda activate {env_}', 
            f'call cd {control_}', 
            f'call mpiexec -n 1 python {test_m_py} {dataset_} {auxgates} '\
                f'{ventstr} : -n 7 {mpilims_} -x -l{test_w_lb}']
        subprocess.call(' && '.join(cmds_test), shell=True)
    
    return 0


def location(dataset_: Path, naux: int, name: str, meshdata, config):
    _, _, gates, vents, _ = meshdata
    _, mpilims_, miniforge_, env_ = config
    
    # make folder
    location_ = Path(name).resolve()
    os.mkdir(location_)
    os.mkdir(location_/'res')
    os.mkdir(location_/'temp')
    
    pos = np.load(dataset_/'../mesh/mesh_flat.npy')
    nnodes = np.size(pos,0)
    
    max_calls = 100
    n_initial_points = round(max_calls/3)
    xdata = np.zeros((max_calls,naux*2))
    ydata = np.zeros(max_calls)
    auxdata = []
    
    bounds = (0.0,1.0)
    optimizer = Optimizer(
        [bounds for _ in range(2*naux)], 
        base_estimator=GaussianProcessRegressor(), 
        n_initial_points=n_initial_points, 
        initial_point_generator='halton', 
        )
    
    i = 0
    with tqdm(total=max_calls) as pbar:
        while i < max_calls:
            locs = np.array(optimizer.ask())
            perms = list(itertools.permutations(np.arange(naux)))
            locperms = []
            for p in perms:
                pp = []
                for j in range(naux):
                    pp.append(p[j]*2)
                    pp.append(p[j]*2+1)
                locperms.append(locs[pp].tolist())
            auxgates = []
            illegal_gate = False
            for j in range(naux):
                locsmtx = np.reshape(locs[2*j:2*j+2],(1,-1))
                d = pos - np.ones((nnodes,1)) @ locsmtx
                distances = np.linalg.norm(d, axis=1)
                auxgate = np.argmin(distances) + 1
                auxgates.append(str(auxgate))
                if np.min(distances) > 0.05:
                    illegal_gate = True
                if auxgate in gates or auxgate in vents:
                    illegal_gate = True
            if len(set(auxgates)) != len(auxgates):  # duplicate nodes
                illegal_gate = True
            if illegal_gate:
                for locperm in locperms:
                    optimizer.tell(locperm, 0)
                continue
            
            auxgates = ','.join(auxgates)
            auxdata.append(auxgates)
            name_i = f'{name}/temp/control{i}'
            control(dataset_, auxgates, name_i, meshdata, config, 
                    location_optim=True)
            res = np.load(f'{name}/temp/control{i}/results.npz')
            bestfills = res['ybest']
            score = np.sum(bestfills > 0.98) / np.size(bestfills)
            
            for locperm in locperms:
                optimizer.tell(locs.tolist(), -1 * score)
            xdata[i,:] = locs
            ydata[i] = score
            i += 1
            pbar.update()
    
    bestind = np.argmax(ydata)
    rtm_rlperdue_ = Path(dataset_/'../../../src/rtm_rlperdue').resolve()
    control_ = location_ / f'temp/control{bestind}'
    test_m_py = Path(rtm_rlperdue_ / 'masters/test_m.py')
    test_w_lb = Path(rtm_rlperdue_ / 'workers/test-LO_w.lb')
    auxgates_best = auxdata[bestind]
    ventstr = ','.join([str(vent) for vent in vents])
    cmds_test = [
        '@echo off', 
        f'call {miniforge_}', 
        f'call conda activate {env_}', 
        f'call cd {control_}', 
        f'call mpiexec -n 1 python {test_m_py} {dataset_} {auxgates_best} '\
            f'{ventstr} : -n 7 {mpilims_} -x -l{test_w_lb}']
    subprocess.call(' && '.join(cmds_test), shell=True)
    
    for file in os.listdir(control_/'res'):
        shutil.copy(control_/f'res/{file}', location_/f'res/{file}')
    
    cummax = [np.max(ydata[:i+1]) for i in range(max_calls)]
    plt.figure()
    plt.plot(range(max_calls), cummax, '.')
    plt.ylim([0,1.1])
    plt.savefig(location_/'convergence.png')
    plt.close()
    
    xbest = xdata[bestind,:]
    ybest = ydata[bestind]
    np.savez(location_/'results.npz', 
             x=xdata, 
             y=ydata, 
             xbest=xbest,
             ybest=ybest)
        
    return 0
