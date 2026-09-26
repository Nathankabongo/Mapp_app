"""RBF — interface prête ; implémentation minimale via scipy si dispo."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def rbf_status() -> dict:
    try:
        from scipy.interpolate import RBFInterpolator  # noqa: F401

        return {
            "status": "DISPONIBLE",
            "method": "RBF (scipy.interpolate.RBFInterpolator)",
            "message": "Moteur prêt — nécessite points de contrôle (forages / contacts).",
            "data_class": "modeled",
        }
    except Exception:
        return {
            "status": "À CONFIGURER",
            "method": "RBF",
            "message": f"{UNAVAILABLE} scipy.interpolate.RBFInterpolator indisponible.",
            "data_class": "unavailable",
        }


def interpolate_rbf(known_xy, known_z, query_xy):
    from scipy.interpolate import RBFInterpolator
    import numpy as np

    known_xy = np.asarray(known_xy, dtype=float)
    known_z = np.asarray(known_z, dtype=float)
    query_xy = np.asarray(query_xy, dtype=float)
    if len(known_xy) < 3:
        raise ValueError("RBF nécessite au moins 3 points")
    rbf = RBFInterpolator(known_xy, known_z)
    return rbf(query_xy), {
        "data_class": "interpolated",
        "method": "RBF",
        "note": "Estimation interpolée — pas une teneur de laboratoire.",
    }
