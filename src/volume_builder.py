"""
3B medikal volume uzerinde kesit secme ve temel bilgi cikarma fonksiyonlari.
"""

from __future__ import annotations

import numpy as np


def get_volume_info(volume: np.ndarray) -> dict[str, object]:
    """Volume boyutu ve temel yogunluk araligini dondurur."""
    return {
        "Volume Shape (Slices, Rows, Columns)": volume.shape,
        "Minimum Value": float(np.min(volume)),
        "Maximum Value": float(np.max(volume)),
        "Mean Value": float(np.mean(volume)),
    }


def get_slice(volume: np.ndarray, plane: str, index: int) -> np.ndarray:
    """Axial, coronal veya sagittal duzlemden 2B kesit alir."""
    plane = plane.lower()

    if plane == "axial":
        index = int(np.clip(index, 0, volume.shape[0] - 1))
        return volume[index, :, :]

    if plane == "coronal":
        index = int(np.clip(index, 0, volume.shape[1] - 1))
        return volume[:, index, :]

    if plane == "sagittal":
        index = int(np.clip(index, 0, volume.shape[2] - 1))
        return volume[:, :, index]

    raise ValueError("Plane degeri axial, coronal veya sagittal olmalidir.")


def get_max_slice_index(volume: np.ndarray, plane: str) -> int:
    """Secilen duzlem icin en buyuk slice indeksini verir."""
    plane = plane.lower()
    if plane == "axial":
        return volume.shape[0] - 1
    if plane == "coronal":
        return volume.shape[1] - 1
    if plane == "sagittal":
        return volume.shape[2] - 1
    raise ValueError("Plane degeri axial, coronal veya sagittal olmalidir.")
