"""Store forages — fichiers locaux uniquement."""

from __future__ import annotations

from pathlib import Path

from compass_core.drillholes.io import assemble_drillholes, load_collars_csv, load_intervals_csv
from compass_core.drillholes.models import Drillhole

DEFAULT_DIR = Path("data/rdc/demo/drillholes")


def load_demo_drillholes() -> list[Drillhole]:
    """Charge les forages DÉMO s'ils existent — jamais d'invention silencieuse."""
    collar_path = DEFAULT_DIR / "collars.csv"
    intervals_path = DEFAULT_DIR / "intervals.csv"
    if not collar_path.exists():
        return []
    collars = load_collars_csv(collar_path)
    intervals = load_intervals_csv(intervals_path) if intervals_path.exists() else []
    return assemble_drillholes(collars, intervals)


def drillhole_count() -> dict:
    holes = load_demo_drillholes()
    return {
        "count": len(holes),
        "status": "DÉMO" if holes else "NON DISPONIBLE",
        "path": str(DEFAULT_DIR),
        "data_class": "demo" if holes else "unavailable",
        "message": (
            f"{len(holes)} forage(s) de démonstration chargés."
            if holes
            else "Aucun forage importé. Importer Collar/Survey/Assay (CSV) pour activer le module."
        ),
    }
