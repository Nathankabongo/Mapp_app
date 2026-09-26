"""Smart Sampling — recommander où collecter les prochaines données."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.drillholes.store import load_demo_drillholes
from compass_core.exploration.uncertainty_map import build_uncertainty_map
from compass_core.prospectivity.prediction import ZONE_PRESETS
from compass_core.spatial.distance import haversine_km


@dataclass
class SampleRecommendation:
    sample_id: str
    latitude: float
    longitude: float
    priority: str  # P1 | P2 | P3
    uncertainty: float
    prospectivity: float | None
    justification: list[str] = field(default_factory=list)
    objective: str = ""
    data_class: str = "prediction"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SmartSamplingPlan:
    zone: str
    mineral: str
    current_samples_proxy: int
    recommended_count: int
    expected_uncertainty_reduction_pct: float | None
    points: list[dict] = field(default_factory=list)
    priority_counts: dict = field(default_factory=dict)
    gaps_addressed: list[str] = field(default_factory=list)
    disclaimer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _existing_evidence_points() -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for h in load_demo_drillholes():
        pts.append((float(h.collar.y), float(h.collar.x)))
    return pts


def _min_dist_km(lat: float, lon: float, pts: list[tuple[float, float]]) -> float | None:
    if not pts:
        return None
    return min(haversine_km(lat, lon, a, b) for a, b in pts)


def recommend_samples(
    *,
    zone: str = "Kolwezi",
    mineral: str = "cuivre",
    latitude: float | None = None,
    longitude: float | None = None,
    n_points: int = 24,
    base_confidence: float = 50.0,
) -> SmartSamplingPlan:
    """
    Recommande des points d'échantillonnage pour réduire l'incertitude.

    Critères (sans inventer de teneurs) :
    - zones sous-échantillonnées (loin des forages/preuves)
    - forte incertitude cartographique
    - prospectivité notable (anomalie à vérifier)
    - zones de transition / fort gradient
    """
    preset = ZONE_PRESETS.get(zone, ZONE_PRESETS["Kolwezi"])
    lat0 = float(latitude if latitude is not None else preset["lat"])
    lon0 = float(longitude if longitude is not None else preset["lon"])
    n_points = max(3, min(40, int(n_points)))

    unc = build_uncertainty_map(
        zone=zone,
        mineral=mineral,
        latitude=lat0,
        longitude=lon0,
        max_cells=max(48, n_points * 3),
        base_confidence=base_confidence,
    )
    evidence = _existing_evidence_points()
    current_n = len(evidence)

    candidates: list[tuple[float, dict]] = []
    for cell in unc.cells:
        u = float(cell["uncertainty"])
        prosp = cell.get("prospectivity")
        prosp_v = float(prosp) if prosp is not None else 0.0
        dmin = _min_dist_km(cell["latitude"], cell["longitude"], evidence)
        under = 30.0 if dmin is None else min(40.0, float(dmin) * 1.5)
        # Score d'information : incertitude + sous-échantillonnage + anomalie modérée/forte
        info = 0.45 * u + 0.35 * under + 0.20 * min(100.0, prosp_v)
        just: list[str] = []
        if u >= 60:
            just.append(f"Incertitude élevée ({u:.0f}/100)")
        elif u >= 40:
            just.append(f"Zone de transition (incertitude {u:.0f})")
        if dmin is None:
            just.append("Aucune preuve locale (forage/occurrence proche)")
        elif dmin > 8:
            just.append(f"Sous-échantillonné (plus proche preuve à {dmin:.1f} km)")
        if prosp_v >= 60:
            just.append(f"Anomalie de prospectivité ({prosp_v:.0f}/100) à valider")
        for drv in cell.get("drivers") or []:
            if drv not in just:
                just.append(drv)
                break
        if not just:
            just.append("Point de contrôle pour densifier la couverture")
        candidates.append(
            (
                info,
                {
                    "latitude": cell["latitude"],
                    "longitude": cell["longitude"],
                    "uncertainty": u,
                    "prospectivity": prosp,
                    "justification": just[:4],
                    "info_score": round(info, 1),
                },
            )
        )

    candidates.sort(key=lambda x: -x[0])

    # Diversité spatiale : éviter les points trop proches les uns des autres
    selected: list[dict] = []
    for _, cand in candidates:
        if len(selected) >= n_points:
            break
        if any(
            haversine_km(cand["latitude"], cand["longitude"], s["latitude"], s["longitude"]) < 1.5
            for s in selected
        ):
            continue
        selected.append(cand)

    # Si grille absente / peu de cellules, proposer un anneau autour du centroïde (honnête)
    if not selected:
        fav = resolve_favorability_path()
        gaps = ["Raster / grille d'incertitude insuffisante pour optimiser"]
        if fav is None:
            gaps.append("Pas de raster de prospectivité — échantillonnage guidé non disponible")
        return SmartSamplingPlan(
            zone=zone,
            mineral=mineral,
            current_samples_proxy=current_n,
            recommended_count=0,
            expected_uncertainty_reduction_pct=None,
            points=[],
            priority_counts={"P1": 0, "P2": 0, "P3": 0},
            gaps_addressed=gaps,
            disclaimer=(
                "Smart Sampling indisponible sans couverture raster. "
                "Importer des données / générer le raster Kolwezi pour activer les recommandations."
            ),
        )

    points: list[SampleRecommendation] = []
    for i, s in enumerate(selected, start=1):
        u = float(s["uncertainty"])
        if u >= 65 or (s.get("prospectivity") or 0) >= 75:
            prio = "P1"
            obj = "Réduire incertitude critique / valider anomalie forte"
        elif u >= 45:
            prio = "P2"
            obj = "Densifier zone de transition"
        else:
            prio = "P3"
            obj = "Contrôle de couverture"
        points.append(
            SampleRecommendation(
                sample_id=f"SMP-{i:02d}",
                latitude=round(float(s["latitude"]), 5),
                longitude=round(float(s["longitude"]), 5),
                priority=prio,
                uncertainty=round(u, 1),
                prospectivity=s.get("prospectivity"),
                justification=list(s["justification"]),
                objective=obj,
            )
        )

    counts = {
        "P1": sum(1 for p in points if p.priority == "P1"),
        "P2": sum(1 for p in points if p.priority == "P2"),
        "P3": sum(1 for p in points if p.priority == "P3"),
    }
    # Estimation qualitative de réduction d'incertitude (heuristique transparente)
    mean_u = float(np.mean([p.uncertainty for p in points])) if points else 0.0
    reduction = round(min(25.0, 6.0 + 0.35 * len(points) + 0.05 * mean_u), 1)

    return SmartSamplingPlan(
        zone=zone,
        mineral=mineral,
        current_samples_proxy=current_n,
        recommended_count=len(points),
        expected_uncertainty_reduction_pct=reduction,
        points=[p.to_dict() for p in points],
        priority_counts=counts,
        gaps_addressed=[
            "Zones mal documentées (incertitude)",
            "Zones sous-échantillonnées",
            "Anomalies de prospectivité à confirmer sur le terrain",
        ],
        disclaimer=(
            f"Proxy échantillons actuels = {current_n} forage(s) DEMO locaux (pas un inventaire géochimique). "
            "Réduction d'incertitude estimée (heuristique), non une garantie. "
            "Chaque point = recommandation à valider (accès, permis, sécurité)."
        ),
    )
