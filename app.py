"""
Tibbi Goruntulemede Dijital Ikiz Teknikleri
DICOM kesitlerinden 3B medikal hacim ve dijital ikiz modeli olusturan Streamlit arayuzu.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tempfile
import time

import streamlit as st

from src.digital_twin import (
    build_model_metrics_table,
    build_status_summary,
)
from src.dicom_loader import (
    DicomLoadError,
    extract_public_metadata,
    get_voxel_spacing,
    load_dicom_series,
)
from src.export_model import export_mesh
from src.preprocessing import datasets_to_volume, preprocess_volume
from src.reconstruction_3d import build_surface_mesh, create_plotly_mesh
from src.visualization_2d import create_slice_figure
from src.volume_builder import get_max_slice_index, get_slice, get_volume_info


DEFAULT_DICOM_PATH = ""


st.set_page_config(
    page_title="DICOM 3D Dijital Ikiz",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_and_prepare(folder_path: str, use_hu: bool, refresh_key: str) -> dict[str, object]:
    """Klasoru okuyup ilk ham volume bilgisini cache'ler."""
    datasets, warnings = load_dicom_series(folder_path)
    volume = datasets_to_volume(datasets, use_hu=use_hu)
    metadata = extract_public_metadata(datasets)
    spacing = get_voxel_spacing(datasets)
    return {
        "datasets": datasets,
        "warnings": warnings,
        "raw_volume": volume,
        "metadata": metadata,
        "spacing": spacing,
        "refresh_key": refresh_key,
    }


def _clear_generated_models() -> None:
    st.session_state.pop("mesh_result", None)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    st.title("DICOM Kesitlerinden 3D Medikal Dijital Ikiz")

    if "refresh_key" not in st.session_state:
        st.session_state["refresh_key"] = 0
    if "last_refresh_at" not in st.session_state:
        st.session_state["last_refresh_at"] = _now_text()

    with st.sidebar:
        st.header("DICOM Klasoru")
        folder_path = st.text_input(
            "DICOM klasor yolu",
            value=DEFAULT_DICOM_PATH,
            help="Windows icin ornek: C:\\Users\\Kullanici\\Desktop\\dicom_klasoru",
        )

        st.header("Dijital Ikiz Guncelleme")
        refresh_clicked = st.button("Veriyi yenile")
        auto_refresh = st.checkbox("Otomatik yenileme", value=False)
        refresh_interval = st.selectbox(
            "Yenileme araligi",
            [30, 60, 120, 300],
            index=1,
            format_func=lambda seconds: f"{seconds} saniye",
            disabled=not auto_refresh,
        )

        st.header("On Isleme")
        use_hu = st.checkbox("Hounsfield Unit donusumu uygula", value=True)
        apply_windowing = st.checkbox("Windowing uygula", value=True)
        window_center = st.number_input("Window center", value=40.0, step=10.0)
        window_width = st.number_input("Window width", value=400.0, min_value=1.0, step=10.0)
        apply_gaussian = st.checkbox("Gaussian filtre uygula", value=False)
        sigma = st.slider("Gaussian sigma", 0.1, 3.0, 1.0, 0.1)

        st.header("3D Model")
        model_threshold = st.slider("Model threshold", 0.0, 1.0, 0.45, 0.01)
        step_size = st.slider(
            "Marching Cubes step size",
            1,
            5,
            1,
            help="Buyuk deger daha hizli fakat daha dusuk ayrintili model uretir.",
        )
        export_format = st.selectbox("Disa aktarim formati", ["STL", "OBJ"])

    if refresh_clicked:
        load_and_prepare.clear()
        st.session_state["refresh_key"] += 1
        st.session_state["last_refresh_at"] = _now_text()
        _clear_generated_models()

    if auto_refresh:
        auto_bucket = int(time.time() // int(refresh_interval))
        if st.session_state.get("auto_refresh_bucket") != auto_bucket:
            st.session_state["auto_refresh_bucket"] = auto_bucket
            st.session_state["last_refresh_at"] = _now_text()
            _clear_generated_models()
        st.markdown(
            f"<meta http-equiv='refresh' content='{int(refresh_interval)}'>",
            unsafe_allow_html=True,
        )
    else:
        auto_bucket = 0

    if not folder_path:
        st.info("Baslamak icin bir DICOM klasor yolu girin.")
        return

    try:
        refresh_key = f"{st.session_state['refresh_key']}-{auto_bucket}"
        loaded = load_and_prepare(folder_path, use_hu, refresh_key)
    except DicomLoadError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"DICOM klasoru islenirken hata olustu: {exc}")
        return

    warnings = loaded["warnings"]
    if warnings:
        with st.expander("Okuma uyarilari"):
            for warning in warnings:
                st.warning(warning)

    raw_volume = loaded["raw_volume"]
    processed_volume = preprocess_volume(
        raw_volume,
        apply_windowing=apply_windowing,
        window_center=window_center,
        window_width=window_width,
        apply_gaussian=apply_gaussian,
        sigma=sigma,
        normalize=True,
    )

    mesh_result = st.session_state.get("mesh_result")
    mesh_state = "3D dijital ikiz modeli uretildi" if mesh_result else "Model bekliyor"
    status_summary = build_status_summary(
        folder_path=folder_path,
        refreshed_at=st.session_state["last_refresh_at"],
        slice_count=len(loaded["datasets"]),
        spacing=loaded["spacing"],
        mesh_state=mesh_state,
    )

    status_col, metadata_col, volume_col = st.columns([1.2, 1, 1])
    with status_col:
        st.subheader("Dijital Ikiz Durumu")
        st.table(status_summary)

    with metadata_col:
        st.subheader("Anonim DICOM Metadata")
        st.table(loaded["metadata"])

    with volume_col:
        st.subheader("Volume Bilgisi")
        st.table(get_volume_info(processed_volume))
        st.write(f"Voxel spacing (z, y, x): {loaded['spacing']}")

    st.divider()

    left_col, right_col = st.columns([1, 1])
    with left_col:
        st.subheader("2D Kesit Goruntuleme")
        plane = st.radio(
            "Kesit duzlemi",
            ["Axial", "Coronal", "Sagittal"],
            horizontal=True,
        )
        max_index = get_max_slice_index(processed_volume, plane)
        slice_index = st.slider("Slice numarasi", 0, max_index, max_index // 2)
        selected_slice = get_slice(processed_volume, plane, slice_index)
        fig = create_slice_figure(selected_slice, f"{plane} Slice #{slice_index}")
        st.pyplot(fig, clear_figure=True)

    with right_col:
        st.subheader("3D Dijital Ikiz")
        st.write("Secilen threshold degeri ile tek bir 3D dijital ikiz modeli uretilir.")

        if st.button("3D dijital ikiz modelini olustur", type="primary"):
            try:
                with st.spinner("3D dijital ikiz modeli olusturuluyor..."):
                    vertices, faces, normals, values = build_surface_mesh(
                        processed_volume,
                        threshold=float(model_threshold),
                        spacing=loaded["spacing"],
                        step_size=step_size,
                    )
                    generated_mesh = {
                        "vertices": vertices,
                        "faces": faces,
                    }
                st.session_state["mesh_result"] = generated_mesh
                mesh_result = generated_mesh
                st.success("3D dijital ikiz modeli olusturuldu.")
            except Exception as exc:
                st.error(f"3D model olusturulamadi: {exc}")

        if mesh_result:
            model_fig = create_plotly_mesh(
                mesh_result["vertices"],
                mesh_result["faces"],
                title="3D Dijital Ikiz Modeli",
            )
            st.plotly_chart(model_fig, use_container_width=True)

            suffix = export_format.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp_file:
                export_path = export_mesh(
                    mesh_result["vertices"],
                    mesh_result["faces"],
                    tmp_file.name,
                )
                file_bytes = Path(export_path).read_bytes()

            st.download_button(
                label=f"3D dijital ikiz modelini {export_format} olarak indir",
                data=file_bytes,
                file_name=f"digital_twin_model.{suffix}",
                mime="application/octet-stream",
            )

    st.divider()
    st.subheader("3D Model Metrikleri")
    model_metric_rows = build_model_metrics_table(
        processed_volume,
        loaded["spacing"],
        model_threshold,
        mesh_result=mesh_result,
    )
    st.table(model_metric_rows)


if __name__ == "__main__":
    main()
