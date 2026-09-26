"""Analyse de densité structurale et proximité des failles géologiques."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter


def compute_fault_density(
    fault_mask: np.ndarray,
    search_radius_px: int = 5,
    sigma: float = 2.0,
) -> np.ndarray:
    """
    Calcule la densité de linéaments structuraux à partir d'un masque binaire de failles.
    """
    if fault_mask.ndim != 2:
        raise ValueError("Le masque de failles doit être 2D.")

    density = gaussian_filter(fault_mask.astype(float), sigma=sigma)
    # Normalisation entre 0 et 1
    max_val = np.max(density)
    if max_val > 0:
        density /= max_val
    return density


def compute_fault_proximity(
    fault_mask: np.ndarray,
    pixel_size_m: float = 50.0,
    max_distance_m: float = 5000.0,
) -> np.ndarray:
    """
    Calcule la carte de proximité euclidienne aux failles (décroissance exponentielle).
    1.0 = sur la faille, 0.0 = au-delà de max_distance_m.
    """
    if fault_mask.ndim != 2:
        raise ValueError("Le masque de failles doit être 2D.")

    # Distance de chaque pixel au pixel 'True' le plus proche
    inv_mask = ~fault_mask.astype(bool)
    distances_px = distance_transform_edt(inv_mask)
    distances_m = distances_px * pixel_size_m

    # Fonction de favorabilité géologique décroissante
    proximity = np.exp(-distances_m / (max_distance_m / 3.0))
    return np.clip(proximity, 0.0, 1.0)
