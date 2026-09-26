"""Extraction des features/labels pour l'apprentissage supervisé."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from compass_core.data.vector import rasterize_samples


@dataclass
class LabeledSamples:
    """Matrice de features et vecteur de labels."""

    features: np.ndarray
    labels: np.ndarray
    sample_count: int


def extract_labeled_samples(
    raster_path: str,
    band_cube: np.ndarray,
    samples_path: str,
    *,
    attribute: str = "raster",
) -> LabeledSamples:
    """
    Extrait X (bandes spectrales/géophysiques) et y (classe binaire) aux points d'échantillons.

    Migré depuis ``Data_preprocessing.dataFitting``.
    """
    truth = rasterize_samples(raster_path, samples_path, attribute=attribute)
    mask = truth > 0
    sample_count = int(mask.sum())

    if sample_count == 0:
        raise ValueError(f"Aucun échantillon valide trouvé dans {samples_path}")

    features = band_cube[mask]
    labels = truth[mask] - 1
    return LabeledSamples(features=features, labels=labels, sample_count=sample_count)
