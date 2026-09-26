"""Population — WorldPop local ou indisponible."""

from __future__ import annotations

from pathlib import Path

WORLDPOP_CANDIDATES = (
    Path("data/rdc/national/worldpop.tif"),
    Path("data/rdc/atlas/population_density.npy"),
)


def worldpop_status() -> dict[str, str]:
    for path in WORLDPOP_CANDIDATES:
        if path.exists():
            kind = "estimated" if path.suffix == ".npy" else "open"
            note = (
                "Raster de densité synthétique (proxy) — pas WorldPop officiel."
                if path.suffix == ".npy"
                else "Raster WorldPop local."
            )
            return {"status": "local", "path": str(path), "data_class": kind, "note": note}
    return {
        "status": "missing",
        "path": "",
        "data_class": "unavailable",
        "note": "WorldPop non intégré. Information non disponible dans les sources utilisées.",
    }
