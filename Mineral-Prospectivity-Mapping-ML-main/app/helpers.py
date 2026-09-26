"""Helpers de visualisation Streamlit."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from compass_core.data.sample_generator import (
    check_dataset_inventory,
    generate_kolwezi_sample_dataset,
)
from compass_core.pipeline.core import PipelineResult

DEFAULT_API_URL = os.getenv("COMPASS_API_URL", "http://127.0.0.1:8000")
DEFAULT_DATA_DIR = "data/rdc/kolwezi"
DEFAULT_SAMPLE_CONFIG = "config/config_rdc_kolwezi_sample.json"

MODEL_LABELS: dict[str, str] = {
    "woe": "Weights of Evidence",
    "rf": "Random Forest",
    "svm": "SVM (RBF)",
    "ann": "Réseau de neurones",
    "cnn": "Conv1D",
}

COMMODITY_LABELS: dict[str, str] = {
    "cu_co": "Cu-Co",
    "li": "Lithium",
    "au": "Or",
    "diamond": "Diamant",
    "coltan": "Coltan",
    "custom": "Personnalisé",
}


def inject_custom_css() -> None:
    """Injecte les styles globaux de l'application."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        .compass-hero {
            background: linear-gradient(135deg, #0F3D2E 0%, #1B6B4A 55%, #2D8F63 100%);
            border-radius: 14px;
            padding: 1.6rem 2rem;
            margin-bottom: 1.5rem;
            color: #FFFFFF;
            box-shadow: 0 8px 24px rgba(15, 61, 46, 0.18);
        }
        .compass-hero h1 {
            margin: 0;
            font-size: 1.85rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #FFFFFF !important;
        }
        .compass-hero p {
            margin: 0.45rem 0 0;
            opacity: 0.92;
            font-size: 0.98rem;
            color: #E8F5EE !important;
        }
        .compass-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.28);
            border-radius: 999px;
            padding: 0.2rem 0.75rem;
            font-size: 0.78rem;
            margin-right: 0.4rem;
            margin-top: 0.75rem;
        }
        .compass-section {
            background: #FFFFFF;
            border: 1px solid #E4E8EE;
            border-radius: 12px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
        }
        .compass-section h3 {
            margin-top: 0;
            margin-bottom: 0.35rem;
            font-size: 1.05rem;
            color: #1A2332;
        }
        .compass-section p {
            margin: 0;
            color: #5A6577;
            font-size: 0.9rem;
        }
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E4E8EE;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            box-shadow: 0 2px 6px rgba(26, 35, 50, 0.04);
        }
        div[data-testid="stMetric"] label {
            color: #5A6577 !important;
            font-size: 0.82rem !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #1B6B4A !important;
            font-weight: 700 !important;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .status-ok {
            background: #E8F7EF;
            color: #1B6B4A;
            border: 1px solid #B8E6CE;
        }
        .status-ko {
            background: #FDECEC;
            color: #B42318;
            border: 1px solid #F5C2C0;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
        .dot-ok { background: #1B6B4A; }
        .dot-ko { background: #D92D20; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Affiche l'en-tête principal."""
    st.markdown(
        """
        <div class="compass-hero">
            <h1>CriticalMineralsCompass</h1>
            <p>Cartographie de prospectivité minérale — République Démocratique du Congo</p>
            <span class="compass-badge">Kolwezi · Cu-Co</span>
            <span class="compass-badge">Offline-first</span>
            <span class="compass-badge">API cloud</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str) -> None:
    """Affiche un titre de section encadré."""
    st.markdown(
        f"""
        <div class="compass-section">
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_inventory(data_dir: str = DEFAULT_DATA_DIR) -> bool:
    """Affiche l'inventaire des fichiers SIG Kolwezi. Retourne True si tout est présent."""
    items = check_dataset_inventory(data_dir)
    core_keys = {"Raster multiphysique", "Gisements Cu-Co", "Échantillons entraînement", "Échantillons test"}
    all_core_present = all(present for label, _, present in items if label in core_keys)

    for label, path, present in items:
        icon = "[OK]" if present else "[MANQUANT]"
        size = ""
        if present and path.suffix in {".tif", ".gpkg"}:
            size_mb = path.stat().st_size / (1024 * 1024)
            size = f" — {size_mb:.2f} Mo"
        st.markdown(f"{icon} **{label}** : `{path}`{size}")

    return all_core_present


def render_dataset_metadata(data_dir: str = DEFAULT_DATA_DIR) -> None:
    """Affiche les métadonnées du jeu Kolwezi si disponibles."""
    meta_path = Path(data_dir) / "metadata.json"
    if not meta_path.exists():
        st.info("Générez le jeu d'exemple pour afficher les métadonnées.")
        return
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Résolution", f"{meta['shape']['rows']}×{meta['shape']['cols']}")
    c2.metric("Bandes", meta["shape"]["bands"])
    c3.metric("Gisements +", meta["deposits"]["positive"])
    c4.metric("Gisements −", meta["deposits"]["negative"])
    st.caption(meta.get("description", ""))

    bands_path = Path(data_dir) / "stack_multiphysics.bands.json"
    if bands_path.exists():
        bands = json.loads(bands_path.read_text(encoding="utf-8"))
        with st.expander("Bandes du raster multiphysique"):
            for band in bands.get("bands", []):
                st.markdown(
                    f"- **B{band['index']} `{band['name']}`** — {band.get('description', '')}"
                )


def generate_sample_dataset(
    data_dir: str = DEFAULT_DATA_DIR,
    *,
    seed: int = 42,
) -> None:
    """Génère le jeu SIG Kolwezi et affiche le résultat."""
    with st.spinner("Génération du jeu de données Kolwezi…"):
        report = generate_kolwezi_sample_dataset(data_dir, seed=seed)
    st.success(
        f"Jeu généré : {report.n_deposits} gisements "
        f"({report.n_positive}+ / {report.n_negative}−), "
        f"{report.rows}×{report.cols} px, {report.nbands} bandes."
    )


def render_api_status(base_url: str = DEFAULT_API_URL) -> None:
    """Affiche le statut de l'API dans la barre latérale."""
    health = check_api_health(base_url)
    if health:
        st.markdown(
            """
            <div class="status-pill status-ok">
                <span class="status-dot dot-ok"></span> API en ligne
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Version {health.get('version', '—')}")
    else:
        st.markdown(
            """
            <div class="status-pill status-ko">
                <span class="status-dot dot-ko"></span> API hors ligne
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Lancez `uvicorn api.main:app`")


def model_label(model: str) -> str:
    """Retourne le libellé lisible d'un modèle."""
    return MODEL_LABELS.get(model, model.upper())


def _configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "#FFFFFF",
            "axes.facecolor": "#FAFBFC",
            "axes.edgecolor": "#D8DEE6",
            "axes.labelcolor": "#3D4A5C",
            "axes.titlecolor": "#1A2332",
            "xtick.color": "#5A6577",
            "ytick.color": "#5A6577",
            "font.size": 10,
        }
    )


def render_metrics(result: PipelineResult, *, model_name: str | None = None) -> None:
    """Affiche les métriques principales en colonnes."""
    st.markdown("#### Résultats")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AUC", f"{result.evaluation.auc:.4f}")
    col2.metric("Kappa", f"{result.evaluation.kappa:.4f}")
    rows, cols = result.prediction_map.shape
    col3.metric("Résolution", f"{rows} × {cols}")
    if model_name:
        col4.metric("Modèle", model_label(model_name))


def render_favorability_map(prediction_map: np.ndarray, *, title: str = "Favorabilité") -> None:
    """Affiche une heatmap matplotlib."""
    _configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(prediction_map, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    ax.set_title(title, fontsize=12, fontweight="600", pad=12)
    ax.set_xlabel("Colonne")
    ax.set_ylabel("Ligne")
    ax.tick_params(length=0)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Score de favorabilité", fontsize=9)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_roc_curve(result: PipelineResult) -> None:
    """Trace la courbe ROC de validation."""
    _configure_matplotlib()
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(
        result.evaluation.fpr,
        result.evaluation.tpr,
        color="#1B6B4A",
        lw=2.2,
        label=f"AUC = {result.evaluation.auc:.3f}",
    )
    ax.plot([0, 1], [0, 1], color="#94A3B8", lw=1, linestyle="--")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Taux de faux positifs")
    ax.set_ylabel("Taux de vrais positifs")
    ax.set_title("Courbe ROC", fontsize=12, fontweight="600", pad=10)
    ax.legend(loc="lower right", frameon=False)
    ax.grid(True, alpha=0.25, linestyle="--")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_results_panel(result: PipelineResult, *, model_name: str) -> None:
    """Affiche carte, courbe ROC et métriques dans un layout structuré."""
    render_metrics(result, model_name=model_name)
    map_col, roc_col = st.columns([1.35, 1], gap="large")
    with map_col:
        render_favorability_map(
            result.prediction_map,
            title=f"Carte de favorabilité — {model_label(model_name)}",
        )
    with roc_col:
        render_roc_curve(result)
    render_outputs(result)


def render_outputs(result: PipelineResult) -> None:
    """Liste les fichiers produits et permet de télécharger la provenance."""
    st.markdown("#### Fichiers produits")
    if not result.output_files:
        st.info("Aucun fichier généré.")
        return

    for file_path in result.output_files:
        path = Path(file_path)
        exists = path.exists()
        col_name, col_status = st.columns([4, 1])
        col_name.code(str(path), language=None)
        col_status.caption("✓ OK" if exists else "— absent")

    if result.provenance_path.exists():
        provenance_text = result.provenance_path.read_text(encoding="utf-8")
        st.download_button(
            label="⬇ Télécharger provenance.json",
            data=provenance_text,
            file_name="provenance.json",
            mime="application/json",
            use_container_width=False,
        )
        with st.expander("Aperçu de la provenance"):
            st.json(json.loads(provenance_text))


def check_api_health(base_url: str = DEFAULT_API_URL) -> dict | None:
    """Vérifie si l'API locale/cloud répond."""
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/health", timeout=3) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None


def fetch_api_token(
    base_url: str,
    username: str,
    password: str,
) -> str | None:
    """Obtient un JWT via POST /v1/auth/token."""
    payload = json.dumps({"username": username, "password": password}).encode()
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/auth/token",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode()).get("access_token")
    except urllib.error.HTTPError:
        return None


def api_run_demo(
    base_url: str,
    *,
    model: str = "woe",
    token: str | None = None,
) -> dict | None:
    """Lance POST /v1/demo sur l'API."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = json.dumps({"model": model, "seed": 42, "output_dir": "outputs/streamlit_api"}).encode()
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/demo",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        raise RuntimeError(f"API {exc.code}: {body}") from exc
