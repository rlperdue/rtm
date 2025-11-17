"""
Russell Perdue
Created 2025/11/09
Last updated 2025/11/13
"""

import itertools
from lims import LimsToolbox
import numpy as np
import os
from pathlib import Path

def make_dataset(mesh_dmp: Path, regions_zon: Path, kvalues: list[float], 
                 resfolder: Path):
    if not os.path.exists(resfolder):
        os.mkdir(resfolder)
    os.mkdir(resfolder / 'out')
    resfolder = resfolder.resolve().as_posix()
    
    lims = LimsToolbox(Path('src/rtm_rlperdue/lb_templates/dataset.lb'), 
                       mesh_dmp, regions_zon)
    
    klist = np.array([i for i in itertools.product(kvalues, 
                                                   repeat=lims.n_regions)])
    np.save(resfolder/Path('out/klist.npy'), klist)
    for k in klist:
        lims.new(k, resfolder=resfolder)
        
    lims.run()
    
    filltimes = lims.extract_data(resfolder)
    np.save(resfolder/Path('out/filltimes.npy'), filltimes)
    lims.cleanup()
