"""Assemblage scène 3D — forages + terrain synthétique local (viz uniquement)."""

from __future__ import annotations

from compass_core.drillholes.models import Drillhole
from compass_core.drillholes.visualization import trajectory_xyz
from compass_core.constants import UNAVAILABLE


LITHO_COLORS = {
    "couverture": "#c4a35a",
    "schiste": "#6b7c8a",
    "roche altérée": "#b5651d",
    "formation favorable": "#2a9d8f",
    "zone minéralisée": "#e63946",
    "roche encaissante": "#8d99ae",
    "default": "#adb5bd",
}


def build_scene(holes: list[Drillhole]) -> dict:
    """Données pour Plotly 3D — pas de volumes inventés."""
    traces = []
    for hole in holes:
        xyz = trajectory_xyz(hole)
        traces.append(
            {
                "type": "drillhole",
                "hole_id": hole.hole_id,
                "x": xyz[:, 0].tolist(),
                "y": xyz[:, 1].tolist(),
                "z": xyz[:, 2].tolist(),
                "data_class": hole.collar.data_class,
                "intervals": [iv.to_dict() for iv in hole.intervals],
            }
        )
    return {
        "traces": traces,
        "layers_available": {
            "terrain": False,
            "geology": False,
            "faults": False,
            "geophysics": False,
            "mineralization_envelope": False,
            "drillholes": bool(traces),
            "prospectivity": False,
        },
        "message": (
            f"{len(traces)} forage(s) visualisables."
            if traces
            else f"{UNAVAILABLE} Importer des forages pour activer Geo Model 3D (V1)."
        ),
        "version": "V1 — forages uniquement",
        "roadmap": ["V2 surfaces lithologiques", "V3 + prospectivité", "V4 géophysique/géochimie", "V5 Next Best Drillhole"],
    }
