"""
Marching Cubes ile 3B yuzey modeli cikarma ve Plotly ile gorsellestirme.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from skimage.measure import marching_cubes


def build_surface_mesh(
    volume: np.ndarray,
    threshold: float,
    spacing: tuple[float, float, float] = (1.0, 1.0, 1.0),
    step_size: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Marching Cubes algoritmasi ile vertices, faces, normals, values dondurur."""
    if volume.ndim != 3:
        raise ValueError("3D model icin volume 3 boyutlu olmalidir.")

    min_value = float(np.min(volume))
    max_value = float(np.max(volume))
    if not (min_value <= threshold <= max_value):
        raise ValueError(
            f"Threshold {threshold:.3f} volume araligi disinda. "
            f"Aralik: {min_value:.3f} - {max_value:.3f}"
        )

    vertices, faces, normals, values = marching_cubes(
        volume,
        level=threshold,
        spacing=spacing,
        step_size=max(1, int(step_size)),
        allow_degenerate=False,
    )
    return vertices, faces, normals, values


def create_plotly_mesh(
    vertices: np.ndarray,
    faces: np.ndarray,
    title: str = "3D Dijital Ikiz Modeli",
) -> go.Figure:
    """Mesh verisini interaktif Plotly figuru olarak hazirlar."""
    x, y, z = vertices[:, 2], vertices[:, 1], vertices[:, 0]
    i, j, k = faces[:, 0], faces[:, 1], faces[:, 2]

    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                color="lightblue",
                opacity=0.55,
                flatshading=True,
                lighting=dict(ambient=0.35, diffuse=0.8, specular=0.2),
            )
        ]
    )
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig
