"""Carte d'incertitude — zones bien / mal connues (sans inventer de données)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from compass_core.analysis.coordinates import utm_to_wgs84, wgs84_to_utm
from compass_core.analysis.favorability import GeoGrid, load_geogrid, pixel_to_utm
from compass_core.analysis.mineral_layers import find_nearby_deposits
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.drillholes.store import load_demo_drillholes
from compass_core.prospectivity.prediction import ZONE_PRESETS
from compass_core.spatial.distance import haversine_km


@dataclass
class UncertaintyCell:
    latitude: float
    longitude: float
    prospectivity: float | None
    uncertainty: float  # 0-100
    class_label: str  # bien_connue | transition | mal_connue | hors_emprise
    drivers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UncertaintyMapReport:
    zone: str
    mineral: str
    latitude: float
    longitude: float
    raster_path: str | None
    summary: dict
    cells: list[dict] = field(default_factory=list)
    zones: dict = field(default_factory=dict)
    disclaimer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _label(u: float, *, in_bounds: bool) -> str:
    if not in_bounds:
        return "hors_emprise"
    if u < 35:
        return "bien_connue"
    if u < 60:
        return "transition"
    return "mal_connue"


def _evidence_distance_km(lat: float, lon: float) -> tuple[float | None, list[str]]:
    """Distance à la preuve la plus proche (occurrence ou forage) — None si rien."""
    drivers: list[str] = []
    dists: list[float] = []
    try:
        nearby = find_nearby_deposits(lat, lon, radius_km=80.0)
        if nearby:
            dists.append(float(nearby[0].distance_km))
            drivers.append(f"occurrence {nearby[0].name or nearby[0].label} à {nearby[0].distance_km:.1f} km")
    except Exception:
        pass
    for h in load_demo_drillholes():
        d = haversine_km(lat, lon, float(h.collar.y), float(h.collar.x))
        dists.append(d)
        if d <= 5:
            drivers.append(f"forage {h.hole_id} à {d:.1f} km")
    if not dists:
        return None, ["Aucune occurrence / forage local — incertitude élevée"]
    return min(dists), drivers


def build_uncertainty_map(
    *,
    zone: str = "Kolwezi",
    mineral: str = "cuivre",
    latitude: float | None = None,
    longitude: float | None = None,
    max_cells: int = 64,
    base_confidence: float = 50.0,
) -> UncertaintyMapReport:
    """
    Construit une grille d'incertitude échantillonnée sur le raster de prospectivité.

    Incertitude = f(éloignement des preuves, gradient local, confiance modèle).
    Hors emprise / sans raster → cellules hors_emprise, pas de valeurs inventées.
    """
    preset = ZONE_PRESETS.get(zone, ZONE_PRESETS["Kolwezi"])
    lat0 = float(latitude if latitude is not None else preset["lat"])
    lon0 = float(longitude if longitude is not None else preset["lon"])
    fav = resolve_favorability_path()

    if fav is None:
        dist, drivers = _evidence_distance_km(lat0, lon0)
        u = 85.0 if dist is None else min(90.0, 40.0 + float(dist))
        cell = UncertaintyCell(
            latitude=lat0,
            longitude=lon0,
            prospectivity=None,
            uncertainty=round(u, 1),
            class_label=_label(u, in_bounds=False),
            drivers=drivers + ["Raster de prospectivité absent"],
        )
        return UncertaintyMapReport(
            zone=zone,
            mineral=mineral,
            latitude=lat0,
            longitude=lon0,
            raster_path=None,
            summary={
                "bien_connue": 0,
                "transition": 0,
                "mal_connue": 1,
                "hors_emprise": 1,
                "mean_uncertainty": cell.uncertainty,
            },
            cells=[cell.to_dict()],
            zones={
                "well_known": [],
                "poorly_known": [cell.to_dict()],
                "data_sparse": [cell.to_dict()],
            },
            disclaimer=(
                "Carte d'incertitude indisponible sans raster. "
                "Point central évalué uniquement via proximité des preuves locales."
            ),
        )

    grid = load_geogrid(fav)
    values = np.asarray(grid.values, dtype=float)
    rows, cols = values.shape
    step = max(1, int(np.ceil(np.sqrt(rows * cols / max(4, max_cells)))))

    cells: list[UncertaintyCell] = []
    # Confiance de base → incertitude de référence
    base_u = max(5.0, 100.0 - float(base_confidence))

    for r in range(step // 2, rows, step):
        for c in range(step // 2, cols, step):
            v = float(values[r, c])
            if not np.isfinite(v):
                continue
            x, y = pixel_to_utm(r, c, grid)
            lat, lon = utm_to_wgs84(x, y, epsg=grid.crs_epsg)
            dist, drivers = _evidence_distance_km(lat, lon)

            # Gradient local = désaccord / instabilité spatiale
            r0, r1 = max(0, r - 1), min(rows, r + 2)
            c0, c1 = max(0, c - 1), min(cols, c + 2)
            window = values[r0:r1, c0:c1]
            grad = float(np.nanstd(window)) if window.size else 0.0

            # Distance aux preuves → hausse d'incertitude (plafonnée)
            if dist is None:
                dist_term = 35.0
                drivers = drivers or ["Zone sans preuve locale"]
            else:
                dist_term = min(40.0, float(dist) * 1.2)

            u = _clip(base_u * 0.55 + dist_term + grad * 80.0, 5.0, 95.0)
            label = _label(u, in_bounds=True)
            if grad > 0.15:
                drivers.append("Fort gradient local (modèle instable spatialement)")
            if dist is not None and dist > 25:
                drivers.append("Preuves éloignées — zone mal documentée")

            cells.append(
                UncertaintyCell(
                    latitude=lat,
                    longitude=lon,
                    prospectivity=round(v * 100.0, 1),
                    uncertainty=round(u, 1),
                    class_label=label,
                    drivers=drivers[:4],
                )
            )

    summary = {
        "bien_connue": sum(1 for c in cells if c.class_label == "bien_connue"),
        "transition": sum(1 for c in cells if c.class_label == "transition"),
        "mal_connue": sum(1 for c in cells if c.class_label == "mal_connue"),
        "hors_emprise": 0,
        "mean_uncertainty": round(float(np.mean([c.uncertainty for c in cells])) if cells else 0.0, 1),
        "n_cells": len(cells),
        "grid_step_px": step,
    }
    well = [c.to_dict() for c in cells if c.class_label == "bien_connue"]
    poor = sorted(
        [c.to_dict() for c in cells if c.class_label == "mal_connue"],
        key=lambda d: -d["uncertainty"],
    )
    sparse = [c.to_dict() for c in cells if "sans preuve" in " ".join(c.drivers).lower() or "éloign" in " ".join(c.drivers).lower()]

    return UncertaintyMapReport(
        zone=zone,
        mineral=mineral,
        latitude=lat0,
        longitude=lon0,
        raster_path=str(Path(fav)),
        summary=summary,
        cells=[c.to_dict() for c in cells],
        zones={
            "well_known": well[:20],
            "poorly_known": poor[:20],
            "data_sparse": sparse[:20],
        },
        disclaimer=(
            "Incertitude cartographique dérivée du raster + proximité des preuves. "
            "Ce n'est pas une carte de réserves. Zones mal connues = priorité d'acquisition de données."
        ),
    )


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def query_uncertainty_at(
    latitude: float,
    longitude: float,
    *,
    zone: str = "Kolwezi",
    mineral: str = "cuivre",
    base_confidence: float = 50.0,
) -> dict:
    """Interroge l'incertitude au point (réutilise la logique carte)."""
    report = build_uncertainty_map(
        zone=zone,
        mineral=mineral,
        latitude=latitude,
        longitude=longitude,
        max_cells=36,
        base_confidence=base_confidence,
    )
    if not report.cells:
        return {"uncertainty": None, "class_label": "hors_emprise", "message": "Donnée indisponible"}
    # Cellule la plus proche du point demandé
    best = min(
        report.cells,
        key=lambda c: haversine_km(latitude, longitude, c["latitude"], c["longitude"]),
    )
    return {
        **best,
        "summary": report.summary,
        "disclaimer": report.disclaimer,
    }
