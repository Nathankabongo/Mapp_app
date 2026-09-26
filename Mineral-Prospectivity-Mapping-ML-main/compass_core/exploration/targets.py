"""Génération automatique de cibles d'exploration depuis la prospectivité."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from compass_core.analysis.coordinates import utm_to_wgs84, wgs84_to_utm
from compass_core.analysis.favorability import (
    extract_hotspots,
    load_geogrid,
    pixel_to_utm,
    query_favorability,
)
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.minerals.profiles import mineral_supports_raster


@dataclass
class ExplorationTarget:
    target_id: str
    mineral: str
    latitude: float
    longitude: float
    prospectivity_score: float  # 0-100
    confidence_pct: float
    area_km2: float
    priority: int
    priority_label: str
    stars: str
    factors: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    data_class: str = "prediction"
    polygon_wkt: str | None = None
    geological_potential: float = 0.0
    data_quality: float = 0.0
    accessibility: float | None = None
    env_constraint: float | None = None
    social_constraint: float | None = None
    exploration_priority_score: float = 0.0
    uncertainty_pct: float = 0.0
    uncertainty_label: str = ""
    factor_scores: dict = field(default_factory=dict)
    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    status: str = "hypothèse"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _uncertainty_label(uncertainty: float) -> str:
    if uncertainty < 25:
        return "faible"
    if uncertainty < 45:
        return "modérée"
    if uncertainty < 65:
        return "élevée"
    return "très élevée"


def _stars(priority: int) -> str:
    filled = max(1, min(5, 6 - priority))
    return "★" * filled + "☆" * (5 - filled)


def _priority_from_score(score: float, conf: float) -> tuple[int, str]:
    # Combine potentiel + confiance (Zone B très élevée / faible confiance → baisse)
    blended = 0.65 * score + 0.35 * conf
    if blended >= 85:
        return 1, "Très forte"
    if blended >= 70:
        return 2, "Forte"
    if blended >= 55:
        return 3, "Modérée"
    if blended >= 40:
        return 4, "Faible"
    return 5, "Très faible"


def _factors(available: list[str], score: float) -> list[str]:
    factors = []
    for layer in available:
        factors.append(f"Couche disponible : {layer}")
    if score >= 70:
        factors.append("Score de prospectivité élevé (prédiction IA)")
    elif score >= 50:
        factors.append("Score de prospectivité moyen (prédiction IA)")
    else:
        factors.append("Score de prospectivité faible — cible secondaire")
    factors.append("Validation terrain : NON EFFECTUÉE")
    return factors


def generate_targets(
    *,
    zone: str,
    mineral: str,
    latitude: float,
    longitude: float,
    max_targets: int = 10,
    base_confidence: float = 50.0,
    available_layers: list[str] | None = None,
    missing_layers: list[str] | None = None,
) -> list[ExplorationTarget]:
    """
    Extrait des cibles depuis le raster de prospectivité (hotspots).
    Si le raster est absent ou le minerai non couvert : liste vide + pas d'invention.
    """
    available = available_layers or []
    missing = missing_layers or []
    if not mineral_supports_raster(mineral):
        return []
    fav_path = resolve_favorability_path()
    if fav_path is None:
        return []

    try:
        grid = load_geogrid(fav_path)
    except Exception:
        return []

    utm_x, utm_y = wgs84_to_utm(latitude, longitude, epsg=grid.crs_epsg)

    # Seuils adaptatifs : chercher des hotspots réels, pas inventés
    hotspots = []
    for thr in (0.75, 0.60, 0.45, 0.35):
        hotspots = extract_hotspots(
            grid,
            center_utm_x=utm_x,
            center_utm_y=utm_y,
            threshold=thr,
            max_distance_m=25000.0,
            max_zones=max_targets,
        )
        if hotspots:
            break

    # Fallback : pics locaux si composantes connexes trop rares
    if not hotspots:
        hotspots = _peak_targets(grid, latitude, longitude, max_targets=max_targets)

    data_quality = min(100.0, 40.0 + 8.0 * len(available))
    targets: list[ExplorationTarget] = []

    for i, hs in enumerate(hotspots[:max_targets], start=1):
        centroid = hs.polygon_wgs84.centroid
        lon_c, lat_c = float(centroid.x), float(centroid.y)
        score = float(hs.score_max) * 100.0
        # Confiance locale : base × couverture données − pénalité superficie très petite
        conf = float(base_confidence)
        if hs.area_km2 < 0.5:
            conf = max(20.0, conf - 10.0)
        conf = min(95.0, conf)
        uncertainty = round(max(0.0, 100.0 - conf), 1)
        priority, plabel = _priority_from_score(score, conf)
        constraints = []
        for m in missing[:5]:
            constraints.append(f"Donnée manquante : {m}")
        constraints.append("Contraintes env./sociales : non quantifiées (NON DISPONIBLE)")
        pos = [f for f in _factors(available, score) if "élevé" in f.lower() or "Couche" in f]
        neg = list(constraints[:3])
        factor_scores = {
            "geology": round(score * 0.85, 1),
            "occurrences": round(min(100.0, 40.0 + 8.0 * len(available)), 1) if available else None,
        }
        # Retirer clés None
        factor_scores = {k: v for k, v in factor_scores.items() if v is not None}

        targets.append(
            ExplorationTarget(
                target_id=f"CIBLE-{i:02d}",
                mineral=mineral,
                latitude=lat_c,
                longitude=lon_c,
                prospectivity_score=round(score, 1),
                confidence_pct=round(conf, 1),
                area_km2=round(float(hs.area_km2), 2),
                priority=priority,
                priority_label=plabel,
                stars=_stars(priority),
                factors=_factors(available, score),
                constraints=constraints,
                data_class="prediction",
                polygon_wkt=hs.polygon_wgs84.wkt,
                geological_potential=round(score, 1),
                data_quality=round(data_quality, 1),
                accessibility=None,
                env_constraint=None,
                social_constraint=None,
                exploration_priority_score=round(0.65 * score + 0.35 * conf, 1),
                uncertainty_pct=uncertainty,
                uncertainty_label=_uncertainty_label(uncertainty),
                factor_scores=factor_scores,
                positive_factors=pos,
                negative_factors=neg,
                methods=["hotspot_prospectivity", "woe_raster_query"],
                status="hypothèse",
                note=(
                    "Cible générée par hotspot de prospectivité IA. "
                    f"Seuil adapté. Source raster : {fav_path.name}."
                ),
            )
        )

    # Toujours inclure le point central interrogé s'il est in_bounds et pas déjà proche
    hit = query_favorability(grid, latitude=latitude, longitude=longitude, commodity="cu_co")
    if hit.in_bounds and hit.score is not None:
        near = any(
            abs(t.latitude - latitude) < 0.01 and abs(t.longitude - longitude) < 0.01 for t in targets
        )
        if not near and len(targets) < max_targets:
            score = float(hit.score) * 100.0
            conf = float(base_confidence)
            uncertainty = round(max(0.0, 100.0 - conf), 1)
            priority, plabel = _priority_from_score(score, conf)
            targets.append(
                ExplorationTarget(
                    target_id=f"CIBLE-{len(targets)+1:02d}",
                    mineral=mineral,
                    latitude=latitude,
                    longitude=longitude,
                    prospectivity_score=round(score, 1),
                    confidence_pct=round(conf, 1),
                    area_km2=0.0,
                    priority=priority,
                    priority_label=plabel,
                    stars=_stars(priority),
                    factors=_factors(available, score) + ["Point d'interrogation zone d'étude"],
                    constraints=[f"Donnée manquante : {m}" for m in missing[:3]],
                    data_class="prediction",
                    geological_potential=round(score, 1),
                    data_quality=round(data_quality, 1),
                    exploration_priority_score=round(0.65 * score + 0.35 * conf, 1),
                    uncertainty_pct=uncertainty,
                    uncertainty_label=_uncertainty_label(uncertainty),
                    factor_scores={"geology": round(score * 0.85, 1)},
                    positive_factors=_factors(available, score)[:2],
                    negative_factors=[f"Donnée manquante : {m}" for m in missing[:2]],
                    methods=["point_query"],
                    status="hypothèse",
                    note="Point central de la zone d'étude (interrogation raster).",
                )
            )

    return targets


def _peak_targets(grid, latitude: float, longitude: float, *, max_targets: int) -> list:
    """Pics locaux sur grille décimée — uniquement valeurs réelles du raster."""
    from compass_core.analysis.favorability import HotspotZone
    from shapely.geometry import box

    values = grid.values
    step = max(1, min(values.shape) // 16)
    peaks = []
    for r in range(step, values.shape[0] - step, step):
        for c in range(step, values.shape[1] - step, step):
            window = values[r - step : r + step + 1, c - step : c + step + 1]
            v = float(values[r, c])
            if v >= float(np.nanmax(window)) and v >= 0.3:
                peaks.append((v, r, c))
    peaks.sort(reverse=True)
    utm_cx, utm_cy = wgs84_to_utm(latitude, longitude, epsg=grid.crs_epsg)
    out = []
    for v, r, c in peaks[:max_targets]:
        x, y = pixel_to_utm(r, c, grid)
        lat, lon = utm_to_wgs84(x, y, epsg=grid.crs_epsg)
        # petit bbox ~ 2 pixels
        x0, y0 = pixel_to_utm(r - 1, c - 1, grid)
        x1, y1 = pixel_to_utm(r + 1, c + 1, grid)
        corners = [utm_to_wgs84(xa, ya, epsg=grid.crs_epsg) for xa, ya in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
        poly = box(
            min(lon_ for _, lon_ in corners),
            min(lat_ for lat_, _ in corners),
            max(lon_ for _, lon_ in corners),
            max(lat_ for lat_, _ in corners),
        )
        dist = float(np.hypot(x - utm_cx, y - utm_cy))
        out.append(
            HotspotZone(
                score_mean=v,
                score_max=v,
                area_km2=max(0.25, (2 * grid.pixel_size_x * 2 * grid.pixel_size_y) / 1e6),
                polygon_wgs84=poly,
                distance_m=dist,
            )
        )
    return out
