"""
Russell Perdue
Created 2025/11/07
Last updated 2025/11/07
"""

from pathlib import Path
import subprocess
import tempfile

def msh2dmp(mesh_msh: Path) -> Path:
    LIMS_PATH = Path(r'C:\lhome\bin\lims.exe')
    
    mesh_msh = mesh_msh.resolve()
    mesh_dmp = mesh_msh.with_suffix('.dmp')
    
    # change back slashes to forward slashes
    mesh_msh = mesh_msh.as_posix()
    mesh_dmp = mesh_dmp.as_posix()
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.lb') as fp:
        fp.write(f'READ "{mesh_msh}"')
        fp.write('\nSETOUTTYPE "dmp"')
        fp.write(f'\nWRITE "{mesh_dmp}"')
        fp.seek(0)
        cmd = f'{LIMS_PATH} -l{fp.name}'
        print(cmd)
        #subprocess.call(cmd)
        print(fp.read())


# %%
mesh_msh = Path('../tests/bpillar.msh')
mesh_msh = msh2dmp(mesh_msh)
