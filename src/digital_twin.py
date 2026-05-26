"""
Dijital ikiz prototipi icin durum ve metrik yardimcilari.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def calculate_volume_metrics(
    volume: np.ndarray,
    threshold: float,
    spacing: tuple[float, float, float],
) -> dict[str, float | int]:
    """Threshold uzerindeki vokseller icin basit hacim metrikleri hesaplar."""
    mask = volume >= threshold
    voxel_count = int(np.count_nonzero(mask))
    voxel_volume = float(np.prod(spacing))
    total_voxels = int(volume.size)

    if voxel_count:
        mean_value = float(np.mean(volume[mask]))
    else:
        mean_value = 0.0

    return {
        "voxel_count": voxel_count,
        "volume_mm3": round(voxel_count * voxel_volume, 2),
        "volume_ratio_percent": round((voxel_count / total_voxels) * 100.0, 2),
        "mean_value": round(mean_value, 4),
    }


def calculate_mesh_metrics(vertices: np.ndarray, faces: np.ndarray) -> dict[str, float | int]:
    """Mesh nokta, yuzey ve yaklasik yuzey alani metriklerini hesaplar."""
    triangles = vertices[faces]
    edge_a = triangles[:, 1] - triangles[:, 0]
    edge_b = triangles[:, 2] - triangles[:, 0]
    areas = np.linalg.norm(np.cross(edge_a, edge_b), axis=1) * 0.5

    return {
        "vertex_count": int(len(vertices)),
        "face_count": int(len(faces)),
        "surface_area_mm2": round(float(np.sum(areas)), 2),
    }


def build_model_metrics_table(
    volume: np.ndarray,
    spacing: tuple[float, float, float],
    threshold: float,
    mesh_result: dict[str, np.ndarray] | None = None,
) -> list[dict[str, Any]]:
    """Tek dijital ikiz modeli icin hacim ve mesh metriklerini tabloya cevirir."""
    volume_metrics = calculate_volume_metrics(volume, float(threshold), spacing)

    if mesh_result is not None:
        mesh_metrics: dict[str, Any] = calculate_mesh_metrics(
            mesh_result["vertices"],
            mesh_result["faces"],
        )
    else:
        mesh_metrics = {
            "vertex_count": "Model uretilmedi",
            "face_count": "Model uretilmedi",
            "surface_area_mm2": "Model uretilmedi",
        }

    return [
        {
            "Threshold": round(float(threshold), 3),
            "Hacim (mm3)": volume_metrics["volume_mm3"],
            "Volume orani (%)": volume_metrics["volume_ratio_percent"],
            "Ortalama deger": volume_metrics["mean_value"],
            "Mesh nokta": mesh_metrics["vertex_count"],
            "Mesh yuzey": mesh_metrics["face_count"],
            "Yuzey alani (mm2)": mesh_metrics["surface_area_mm2"],
        }
    ]


def build_status_summary(
    folder_path: str,
    refreshed_at: str,
    slice_count: int,
    spacing: tuple[float, float, float],
    mesh_state: str,
) -> dict[str, Any]:
    """Arayuzde gosterilecek kisa dijital ikiz durum ozetini olusturur."""
    return {
        "Veri kaynagi": str(Path(folder_path)),
        "Son yenileme": refreshed_at,
        "Slice sayisi": slice_count,
        "Voxel spacing (z, y, x)": tuple(round(float(value), 4) for value in spacing),
        "Model durumu": mesh_state,
    }
