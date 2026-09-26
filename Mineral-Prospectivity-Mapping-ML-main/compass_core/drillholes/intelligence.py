"""Drillhole Intelligence — relier cibles ↔ forages ↔ intervalles (sans inventer d'assays)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from compass_core.constants import UNAVAILABLE
from compass_core.drillholes.models import Drillhole
from compass_core.drillholes.store import drillhole_count, load_demo_drillholes
from compass_core.drillholes.visualization import mineralized_segments
from compass_core.spatial.distance import haversine_km


@dataclass
class DrillholeLink:
    hole_id: str
    distance_km: float
    latitude: float
    longitude: float
    depth_m: float
    azimuth: float
    dip: float
    status: str  # proche | distant | hors_rayon
    has_assays: bool
    mineralized_intervals: int
    intervals_summary: list[dict] = field(default_factory=list)
    data_class: str = "demo"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _hole_has_assays(hole: Drillhole) -> bool:
    return any(iv.assay_value is not None for iv in hole.intervals)


def enrich_hole(hole: Drillhole) -> dict:
    """Fiche enrichie d'un forage — assays absents = explicitement indisponibles."""
    segs = mineralized_segments(hole)
    assays = []
    for iv in hole.intervals:
        assays.append(
            {
                "from_m": iv.from_m,
                "to_m": iv.to_m,
                "lithology": iv.lithology or UNAVAILABLE,
                "alteration": iv.alteration or "",
                "mineralization": iv.mineralization or "",
                "element": iv.assay_element or UNAVAILABLE,
                "value": iv.assay_value if iv.assay_value is not None else UNAVAILABLE,
                "unit": iv.assay_unit or UNAVAILABLE,
                "data_class": iv.assay_data_class,
            }
        )
    return {
        "hole_id": hole.hole_id,
        "collar": {
            "longitude": hole.collar.x,
            "latitude": hole.collar.y,
            "elevation_m": hole.collar.z,
            "azimuth": hole.collar.azimuth,
            "dip": hole.collar.dip,
            "depth_m": hole.collar.depth_m,
            "crs": hole.collar.crs,
            "data_class": hole.collar.data_class,
            "source": hole.collar.source,
        },
        "n_intervals": len(hole.intervals),
        "n_surveys": len(hole.surveys),
        "has_assays": _hole_has_assays(hole),
        "assays": assays,
        "mineralized_segments": segs,
        "disclaimer": (
            "Sans analyse laboratoire, les teneurs restent NON DISPONIBLES. "
            "Intervalles minéralisés = lithologie / indices — pas une teneur."
        ),
    }


def link_targets_to_drillholes(
    targets: list[dict],
    *,
    radius_km: float = 15.0,
    holes: list[Drillhole] | None = None,
) -> dict:
    """
    Pour chaque cible, liste les forages dans un rayon.
    Statut ✓ si forage proche, ✗ si aucun.
    """
    holes = holes if holes is not None else load_demo_drillholes()
    info = drillhole_count()
    tree: dict[str, dict] = {}

    for t in targets:
        tid = t.get("target_id", "?")
        lat = float(t.get("latitude") or 0)
        lon = float(t.get("longitude") or 0)
        links: list[DrillholeLink] = []
        for h in holes:
            d = haversine_km(lat, lon, float(h.collar.y), float(h.collar.x))
            if d > radius_km:
                continue
            segs = mineralized_segments(h)
            links.append(
                DrillholeLink(
                    hole_id=h.hole_id,
                    distance_km=round(d, 2),
                    latitude=float(h.collar.y),
                    longitude=float(h.collar.x),
                    depth_m=float(h.collar.depth_m),
                    azimuth=float(h.collar.azimuth),
                    dip=float(h.collar.dip),
                    status="proche" if d <= 5 else "distant",
                    has_assays=_hole_has_assays(h),
                    mineralized_intervals=len(segs),
                    intervals_summary=segs[:5],
                    data_class=h.collar.data_class,
                    note=(
                        "Assays disponibles"
                        if _hole_has_assays(h)
                        else "Assays NON DISPONIBLES (pas de teneur inventée)"
                    ),
                )
            )
        links.sort(key=lambda x: x.distance_km)
        tree[tid] = {
            "target_id": tid,
            "prospectivity": t.get("prospectivity_score"),
            "mark": "✓" if links else "✗",
            "n_holes": len(links),
            "holes": [lk.to_dict() for lk in links],
            "chain": (
                f"{tid} → " + ", ".join(f"{lk.hole_id} {('✓' if lk.mineralized_intervals else '·')}" for lk in links)
                if links
                else f"{tid} → aucun forage ≤ {radius_km} km"
            ),
        }

    return {
        "radius_km": radius_km,
        "drillhole_store": info,
        "targets": tree,
        "orphan_holes": [
            {
                "hole_id": h.hole_id,
                "latitude": h.collar.y,
                "longitude": h.collar.x,
                "linked_targets": [
                    tid
                    for tid, node in tree.items()
                    if any(x["hole_id"] == h.hole_id for x in node["holes"])
                ],
            }
            for h in holes
        ],
        "disclaimer": (
            "Lien spatial cible↔forage uniquement. "
            "Pas d'inférence de teneur. Forages DEMO = pédagogiques."
        ),
    }


def target_drillhole_intelligence(
    target: dict,
    *,
    radius_km: float = 15.0,
) -> dict:
    """Vue détaillée pour une cible + fiches forages enrichies."""
    bundle = link_targets_to_drillholes([target], radius_km=radius_km)
    tid = target.get("target_id", "?")
    node = bundle["targets"].get(tid, {})
    holes_by_id = {h.hole_id: h for h in load_demo_drillholes()}
    enriched = []
    for link in node.get("holes") or []:
        h = holes_by_id.get(link["hole_id"])
        if h:
            enriched.append({**link, "detail": enrich_hole(h)})
    return {
        "target": {
            "id": tid,
            "latitude": target.get("latitude"),
            "longitude": target.get("longitude"),
            "mineral": target.get("mineral"),
            "prospectivity": target.get("prospectivity_score"),
        },
        "mark": node.get("mark", "✗"),
        "chain": node.get("chain"),
        "holes": enriched,
        "disclaimer": bundle["disclaimer"],
    }
