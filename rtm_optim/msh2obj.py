"""
Russell Perdue
Created 2025/11/09
Last updated 2025/11/09
"""

import meshio
from pathlib import Path

def msh2obj(mesh_msh: Path) -> Path:
    mesh = meshio.read(mesh_msh)
    mesh_obj = mesh_msh.with_suffix('.obj')
    meshio.write(mesh_obj, mesh)
    return mesh_obj
