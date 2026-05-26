"""
DICOM klasorlerini okumak ve guvenli metadata cikarmak icin yardimci fonksiyonlar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pydicom
from pydicom.dataset import FileDataset


class DicomLoadError(Exception):
    """DICOM klasoru okunamadiginda kullanici dostu hata icin ozel sinif."""


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sort_key(dataset: FileDataset, fallback_index: int) -> tuple[int, float, int]:
    """DICOM kesitlerini en guvenilir bulunan bilgiye gore siralar.

    Oncelik:
    1. ImagePositionPatient z koordinati
    2. SliceLocation
    3. InstanceNumber
    4. Dosya okuma sirasi
    """
    image_position = getattr(dataset, "ImagePositionPatient", None)
    if image_position is not None and len(image_position) >= 3:
        return (0, _safe_float(image_position[2]), fallback_index)

    slice_location = getattr(dataset, "SliceLocation", None)
    if slice_location is not None:
        return (1, _safe_float(slice_location), fallback_index)

    instance_number = getattr(dataset, "InstanceNumber", None)
    if instance_number is not None:
        return (2, _safe_float(instance_number), fallback_index)

    return (3, float(fallback_index), fallback_index)


def find_dicom_files(folder_path: str | Path) -> list[Path]:
    """Klasor icindeki .dcm dosyalarini bulur.

    Bazı merkezler DICOM dosyalarini uzantisiz kaydedebilir. Bu proje istenen
    kapsam geregi once .dcm dosyalarini arar; bulunamazsa klasordeki tum dosyalari
    okuyarak DICOM olup olmadigini pydicom ile denemeye birakir.
    """
    folder = Path(folder_path).expanduser()
    if not folder.exists() or not folder.is_dir():
        raise DicomLoadError("Gecerli bir DICOM klasoru secilmedi.")

    dcm_files = sorted(folder.rglob("*.dcm"))
    if dcm_files:
        return dcm_files

    return [path for path in sorted(folder.rglob("*")) if path.is_file()]


def load_dicom_series(folder_path: str | Path) -> tuple[list[FileDataset], list[str]]:
    """DICOM klasorunu okur, hatali dosyalari atlar ve kesitleri siralar."""
    files = find_dicom_files(folder_path)
    datasets: list[FileDataset] = []
    warnings: list[str] = []

    for file_path in files:
        try:
            dataset = pydicom.dcmread(str(file_path), force=True)
            if not hasattr(dataset, "PixelData"):
                warnings.append(f"Piksel verisi yok, atlandi: {file_path.name}")
                continue
            datasets.append(dataset)
        except Exception as exc:
            warnings.append(f"Okunamayan dosya atlandi: {file_path.name} ({exc})")

    if not datasets:
        raise DicomLoadError("Klasorde okunabilir DICOM goruntu dosyasi bulunamadi.")

    sorted_pairs = sorted(
        enumerate(datasets),
        key=lambda item: _sort_key(item[1], item[0]),
    )
    sorted_datasets = [dataset for _, dataset in sorted_pairs]
    return sorted_datasets, warnings


def extract_public_metadata(datasets: list[FileDataset]) -> dict[str, Any]:
    """Kisisel bilgi icermeyen teknik metadata dondurur."""
    first = datasets[0]
    pixel_spacing = getattr(first, "PixelSpacing", ["Bilinmiyor", "Bilinmiyor"])

    return {
        "Hasta": "Anonim",
        "Modality": getattr(first, "Modality", "Bilinmiyor"),
        "Slice Thickness": getattr(first, "SliceThickness", "Bilinmiyor"),
        "Pixel Spacing": list(pixel_spacing) if pixel_spacing is not None else "Bilinmiyor",
        "Rows": getattr(first, "Rows", "Bilinmiyor"),
        "Columns": getattr(first, "Columns", "Bilinmiyor"),
        "Number of Slices": len(datasets),
        "Photometric Interpretation": getattr(first, "PhotometricInterpretation", "Bilinmiyor"),
    }


def get_voxel_spacing(datasets: list[FileDataset]) -> tuple[float, float, float]:
    """Volume icin z, y, x sirasi ile voxel araliklarini hesaplar."""
    first = datasets[0]
    pixel_spacing = getattr(first, "PixelSpacing", [1.0, 1.0])
    y_spacing = _safe_float(pixel_spacing[0], 1.0)
    x_spacing = _safe_float(pixel_spacing[1], 1.0)

    z_spacing = _safe_float(getattr(first, "SliceThickness", None), 1.0)
    if len(datasets) >= 2:
        z_values: list[float] = []
        for dataset in datasets:
            image_position = getattr(dataset, "ImagePositionPatient", None)
            if image_position is not None and len(image_position) >= 3:
                z_values.append(_safe_float(image_position[2]))
        if len(z_values) >= 2:
            diffs = np.diff(sorted(z_values))
            non_zero_diffs = np.abs(diffs[np.abs(diffs) > 1e-6])
            if non_zero_diffs.size > 0:
                z_spacing = float(np.median(non_zero_diffs))

    return (z_spacing, y_spacing, x_spacing)
