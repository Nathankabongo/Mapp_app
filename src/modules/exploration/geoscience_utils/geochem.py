"""Traitement des données géochimiques compositionnelles (CoDA) et détection d'anomalies."""

from __future__ import annotations

import numpy as np
import pandas as pd


def centered_log_ratio(df: pd.DataFrame, elements: list[str]) -> pd.DataFrame:
    """
    Applique la transformation Centered Log-Ratio (CLR) d'Aitchison.
    Indispensable pour éliminer l'effet de fermeture des données géochimiques (ppm ou %).
    """
    sub_df = df[elements].copy()
    # Remplacement des valeurs sous limite de détection (<=0) par une fraction minimale
    min_positive = sub_df[sub_df > 0].min().min()
    epsilon = (min_positive * 0.5) if (min_positive > 0 and not np.isnan(min_positive)) else 1e-4
    sub_df = sub_df.clip(lower=epsilon)

    # Moyenne géométrique par échantillon (ligne)
    log_vals = np.log(sub_df)
    geom_mean = log_vals.mean(axis=1)

    clr_df = log_vals.sub(geom_mean, axis=0)
    clr_df.columns = [f"{col}_clr" for col in elements]
    return clr_df


def multivariate_anomaly_score(
    df: pd.DataFrame,
    target_elements: list[str],
    weights: dict[str, float] | None = None,
) -> np.ndarray:
    """
    Calcule un indice géochimique multi-élémentaire pondéré pour cibler des gisements types.
    Exemple Katanga : 0.6*Cu + 0.4*Co normalisés.
    """
    if weights is None:
        weights = {elem: 1.0 / len(target_elements) for elem in target_elements}

    # Normalisation robuste par médiane et écart interquartile (MAD)
    normalized_scores = np.zeros(len(df))
    for elem in target_elements:
        vals = df[elem].values
        median = np.nanmedian(vals)
        mad = np.nanmedian(np.abs(vals - median)) + 1e-5
        z_robust = (vals - median) / mad
        w = weights.get(elem, 1.0)
        normalized_scores += w * np.maximum(0, z_robust)

    return normalized_scores
