"""
3B mesh modelini STL veya OBJ formatinda disari aktarma fonksiyonlari.
"""

from __future__ import annotations

from pathlib import Path

import meshio
import numpy as np


def export_mesh(
    vertices: np.ndarray,
    faces: np.ndarray,
    output_path: str | Path,
) -> Path:
    """Vertices/faces verisini dosya uzantisina gore STL veya OBJ olarak kaydeder."""
    path = Path(output_path)
    extension = path.suffix.lower()

    if extension not in {".stl", ".obj"}:
        raise ValueError("Disari aktarim icin .stl veya .obj uzantisi kullanin.")

    path.parent.mkdir(parents=True, exist_ok=True)
    mesh = meshio.Mesh(points=vertices, cells=[("triangle", faces.astype(np.int32))])
    meshio.write(path, mesh)
    return path
