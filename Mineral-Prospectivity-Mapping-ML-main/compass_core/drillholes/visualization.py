"""Trajectoires 3D des forages (simple, dip constant)."""

from __future__ import annotations

import math

import numpy as np

from compass_core.drillholes.models import Drillhole


def trajectory_xyz(hole: Drillhole, *, step_m: float = 5.0) -> np.ndarray:
    """
    Retourne Nx3 (x, y, z) en coordonnées locales relatives au collar.
    Convention : x=est, y=nord, z=élévation (décroît avec la profondeur).
    Si CRS = EPSG:4326, x/y sont en degrés — pour viz locale on convertit
    en mètres approximatifs via facteur cos(lat).
    """
    c = hole.collar
    depth = max(c.depth_m, 1.0)
    n = max(2, int(depth / step_m) + 1)
    depths = np.linspace(0.0, depth, n)

    az = math.radians(c.azimuth)
    dip = math.radians(c.dip)  # -90 vertical down
    # Plunge toward depth
    horiz = math.cos(abs(dip)) if abs(c.dip) < 90 else 0.0
    vert = math.sin(abs(dip)) if c.dip <= 0 else -math.sin(abs(dip))

    # Conversion locale mètres si lon/lat
    if "4326" in (c.crs or ""):
        m_per_deg_lat = 111_320.0
        m_per_deg_lon = 111_320.0 * math.cos(math.radians(c.y))
        x0, y0, z0 = 0.0, 0.0, c.z
        xs, ys, zs = [], [], []
        for d in depths:
            dx = d * horiz * math.sin(az)
            dy = d * horiz * math.cos(az)
            dz = -d * abs(vert) if c.dip <= 0 else d * vert
            xs.append(x0 + dx)
            ys.append(y0 + dy)
            zs.append(z0 + dz)
        return np.column_stack([xs, ys, zs])

    xs, ys, zs = [], [], []
    for d in depths:
        dx = d * horiz * math.sin(az)
        dy = d * horiz * math.cos(az)
        dz = -d * abs(vert) if c.dip <= 0 else d * vert
        xs.append(c.x + dx)
        ys.append(c.y + dy)
        zs.append(c.z + dz)
    return np.column_stack([xs, ys, zs])


def mineralized_segments(hole: Drillhole) -> list[dict]:
    """Intersections marquées minéralisées (sans inventer de teneurs)."""
    segs = []
    for iv in hole.intervals:
        if iv.mineralization or (iv.assay_value is not None):
            length = max(0.0, iv.to_m - iv.from_m)
            segs.append(
                {
                    "hole_id": hole.hole_id,
                    "from_m": iv.from_m,
                    "to_m": iv.to_m,
                    "length_m": length,
                    "lithology": iv.lithology,
                    "mineralization": iv.mineralization,
                    "assay_element": iv.assay_element,
                    "assay_value": iv.assay_value,
                    "assay_unit": iv.assay_unit,
                    "assay_data_class": iv.assay_data_class,
                }
            )
    return segs
