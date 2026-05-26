"""
2B medikal kesitleri matplotlib ile gorsellestirme fonksiyonlari.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def create_slice_figure(image: np.ndarray, title: str = "DICOM Slice") -> plt.Figure:
    """Streamlit icinde gosterilebilecek matplotlib figuru olusturur."""
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(image, cmap="gray")
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    return fig
