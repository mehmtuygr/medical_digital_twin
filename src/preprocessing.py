"""
DICOM kesitlerini numpy hacmine donusturme ve basit on isleme fonksiyonlari.

Derin ogrenme veya makine ogrenmesi kullanilmaz. Islemler klasik goruntu isleme
adimlaridir: HU donusumu, windowing, normalizasyon ve opsiyonel Gaussian filtre.
"""

from __future__ import annotations

import numpy as np
from pydicom.dataset import FileDataset
from scipy.ndimage import gaussian_filter


def apply_hounsfield_units(dataset: FileDataset, image: np.ndarray) -> np.ndarray:
    """RescaleSlope ve RescaleIntercept varsa piksel degerlerini HU'ya cevirir."""
    slope = float(getattr(dataset, "RescaleSlope", 1.0))
    intercept = float(getattr(dataset, "RescaleIntercept", 0.0))
    return image.astype(np.float32) * slope + intercept


def datasets_to_volume(datasets: list[FileDataset], use_hu: bool = True) -> np.ndarray:
    """DICOM dataset listesini z, y, x eksenlerinde 3B numpy volume haline getirir."""
    slices: list[np.ndarray] = []

    for dataset in datasets:
        image = dataset.pixel_array.astype(np.float32)

        if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
            image = image.max() - image

        if use_hu:
            image = apply_hounsfield_units(dataset, image)

        slices.append(image)

    try:
        return np.stack(slices, axis=0).astype(np.float32)
    except ValueError as exc:
        raise ValueError(
            "DICOM kesit boyutlari birbiriyle uyusmuyor. Ayni seriye ait dosyalari secin."
        ) from exc


def apply_window(volume: np.ndarray, center: float, width: float) -> np.ndarray:
    """Window center/width kullanarak goruntu kontrastini sinirlar."""
    if width <= 0:
        raise ValueError("Window width 0'dan buyuk olmalidir.")

    lower = center - width / 2
    upper = center + width / 2
    return np.clip(volume, lower, upper)


def normalize_volume(volume: np.ndarray) -> np.ndarray:
    """Volume degerlerini 0-1 araligina normalize eder."""
    volume = volume.astype(np.float32)
    min_value = float(np.nanmin(volume))
    max_value = float(np.nanmax(volume))

    if np.isclose(max_value, min_value):
        return np.zeros_like(volume, dtype=np.float32)

    return (volume - min_value) / (max_value - min_value)


def preprocess_volume(
    volume: np.ndarray,
    apply_windowing: bool = True,
    window_center: float = 40.0,
    window_width: float = 400.0,
    apply_gaussian: bool = False,
    sigma: float = 1.0,
    normalize: bool = True,
) -> np.ndarray:
    """Secilen on isleme adimlarini sirasiyla uygular."""
    processed = volume.astype(np.float32)

    if apply_windowing:
        processed = apply_window(processed, window_center, window_width)

    if apply_gaussian:
        processed = gaussian_filter(processed, sigma=sigma)

    if normalize:
        processed = normalize_volume(processed)

    return processed.astype(np.float32)
