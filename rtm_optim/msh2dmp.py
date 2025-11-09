"""
Russell Perdue
Created 2025/11/07
Last updated 2025/11/09
"""

import os
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile

def msh2dmp(mesh_msh: Path) -> Path:
    LIMS_PATH = Path(r'C:\lhome\bin\lims.exe')
    
    mesh_msh = mesh_msh.resolve()
    mesh_dmp = mesh_msh.with_suffix('.dmp')
    
    # change back slashes to forward slashes
    mesh_msh = mesh_msh.as_posix()
    mesh_dmp = mesh_dmp.as_posix()
    
    # create temporary .lb file
    with NamedTemporaryFile(mode='w', suffix='.lb', delete=False) as fp:
        fp.write(f'READ "{mesh_msh}"')
        fp.write('\nSETOUTTYPE "dmp"')
        fp.write(f'\nWRITE "{mesh_dmp}"')
        fp.seek(0)
    
    # execute and remove .lb file
    cmd = f'{LIMS_PATH} -l{fp.name}'
    subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(fp.name)
    
    return Path(mesh_dmp)
