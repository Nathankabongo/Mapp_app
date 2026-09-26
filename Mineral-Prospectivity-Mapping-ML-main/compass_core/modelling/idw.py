"""Interpolation IDW — estimation explicite, jamais présentée comme mesure."""

from __future__ import annotations

import numpy as np


def idw(
    known_xy: np.ndarray,
    known_z: np.ndarray,
    query_xy: np.ndarray,
    *,
    power: float = 2.0,
    max_distance: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (values, confidence_proxy 0-1).
    confidence_proxy = inverse distance normalized — pas une variance géostatistique.
    """
    if len(known_xy) == 0:
        raise ValueError("Aucun point connu pour IDW")
    vals = []
    confs = []
    for q in query_xy:
        d = np.linalg.norm(known_xy - q, axis=1)
        d = np.maximum(d, 1e-9)
        if max_distance is not None:
            mask = d <= max_distance
            if not mask.any():
                vals.append(np.nan)
                confs.append(0.0)
                continue
            d = d[mask]
            z = known_z[mask]
        else:
            z = known_z
        w = 1.0 / (d**power)
        vals.append(float(np.sum(w * z) / np.sum(w)))
        confs.append(float(1.0 / (1.0 + np.min(d) / 100.0)))
    return np.array(vals), np.array(confs)
