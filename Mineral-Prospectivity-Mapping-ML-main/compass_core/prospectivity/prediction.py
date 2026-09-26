"""Moteur de prospectivité — nationale ; raster pilote Kolwezi Cu-Co uniquement."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from compass_core.analysis.favorability import load_geogrid, query_favorability
from compass_core.analysis.national import locate_province
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.constants import FAVORABILITY_BANDS
from compass_core.gis.crs import resolve_metric_crs
from compass_core.minerals.profiles import mineral_supports_raster
from compass_core.models.prospectivity import classify_score
from compass_core.prospectivity.features import assess_features
from compass_core.prospectivity.validation import ConfidenceReport, build_confidence_report

# Localités de référence (rétrocompat) — la campagne utilise désormais les provinces
ZONE_PRESETS = {
    "Kolwezi": {"lat": -10.716, "lon": 25.465, "province": "Lualaba", "mineral_default": "cuivre"},
    "Likasi": {"lat": -10.983, "lon": 26.733, "province": "Haut-Katanga", "mineral_default": "cuivre"},
    "Lubumbashi": {"lat": -11.664, "lon": 27.479, "province": "Haut-Katanga", "mineral_default": "cuivre"},
    "Tenke": {"lat": -10.600, "lon": 26.150, "province": "Lualaba", "mineral_default": "cuivre"},
    "Manono": {"lat": -7.283, "lon": 27.400, "province": "Tanganyika", "mineral_default": "lithium"},
    "Kibali": {"lat": 3.120, "lon": 29.450, "province": "Haut-Uélé", "mineral_default": "or"},
    "Twangiza": {"lat": -2.950, "lon": 28.650, "province": "Sud-Kivu", "mineral_default": "or"},
    "Kamituga": {"lat": -3.067, "lon": 28.183, "province": "Sud-Kivu", "mineral_default": "or"},
    "Mbuji-Mayi": {"lat": -6.150, "lon": 23.600, "province": "Kasaï-Oriental", "mineral_default": "diamant"},
    "Tshikapa": {"lat": -6.416, "lon": 20.800, "province": "Kasaï", "mineral_default": "diamant"},
    "Kinshasa": {"lat": -4.325, "lon": 15.322, "province": "Kinshasa", "mineral_default": None},
    "Personnalisée": {"lat": -4.0375, "lon": 21.7587, "province": "RDC", "mineral_default": None},
}

NE_LABEL = "N/E"
NE_MESSAGE = (
    "Non évalué — aucune carte raster de prospectivité disponible "
    "pour cette zone et ce minerai (ou point hors emprise pilote)."
)


@dataclass
class ProspectivityResult:
    country: str
    province: str
    zone: str
    mineral: str
    latitude: float
    longitude: float
    metric_crs: str
    prospectivity_pct: float | None  # None = N/E (jamais 0 artificiel)
    prospectivity_level: str
    model_confidence_pct: float
    available_layers: list[str]
    missing_layers: list[str]
    evidence_stage: str
    model_used: str
    raster_path: str | None
    in_bounds: bool
    disclaimer: str
    recommendation_hint: str
    status: str = "evaluated"  # evaluated | N/E
    ne_guidance: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _level_from_score(score: float) -> str:
    for lo, hi, label in FAVORABILITY_BANDS:
        if lo <= score < hi:
            mapping = {
                "Très faible": "TRÈS FAIBLE",
                "Faible": "FAIBLE",
                "Modérée": "MOYENNE",
                "Moyenne": "MOYENNE",
                "Élevée": "FORTE",
                "Forte": "FORTE",
                "Très élevée": "TRÈS FORTE",
                "Très forte": "TRÈS FORTE",
            }
            return mapping.get(label, label.upper())
    return "TRÈS FORTE"


def _recommendation(level: str, conf: float, in_bounds: bool, *, is_ne: bool) -> str:
    if is_ne:
        return (
            "Prospectivité N/E — compléter géologie / géochimie / géophysique / satellite "
            "puis construire un modèle pour ce couple Minerai × Zone."
        )
    if not in_bounds:
        return "Zone à étudier davantage — score non évalué (hors emprise des données modèle)."
    if level in {"TRÈS FORTE", "FORTE"} and conf >= 60:
        return "Potentiel élevé (prédictif) — prioriser validation terrain et croisement CAMI."
    if level == "MOYENNE":
        return "Potentiel moyen — compléter géochimie / géologie avant décision d'exploration."
    if level in {"FAIBLE", "TRÈS FAIBLE"}:
        return "Potentiel faible selon le modèle — ne pas interpréter comme absence absolue de minéralisation."
    return "Zone présentant des contraintes de données importantes."


def run_prospectivity(
    *,
    zone: str = "Kolwezi",
    mineral: str = "cuivre",
    latitude: float | None = None,
    longitude: float | None = None,
    model: str = "woe",
    province: str | None = None,
) -> ProspectivityResult:
    """
    Prospectivité nationale.

    Score numérique uniquement si le point tombe dans l'emprise du raster pilote
    Cu-Co Kolwezi et que le minerai est supporté. Sinon : prospectivity_pct=None, level=N/E.
    """
    from compass_core.minerals.zone_knowledge import (
        normalize_province_name,
        prospectivity_ne_recommendation,
        province_center,
    )

    preset = ZONE_PRESETS.get(zone)
    if latitude is not None and longitude is not None:
        lat, lon = float(latitude), float(longitude)
    elif preset:
        lat, lon = float(preset["lat"]), float(preset["lon"])
    elif province:
        lat, lon = province_center(province)
    else:
        lat, lon = province_center("Lualaba")

    located, _basin = locate_province(lat, lon)
    prov = normalize_province_name(province or located or (preset or {}).get("province") or "RDC")
    crs = resolve_metric_crs(lat, lon)
    features = assess_features(province=prov, mineral=mineral)

    fav_path = resolve_favorability_path()
    prospectivity_pct: float | None = None
    level = NE_LABEL
    in_bounds = False
    model_used = model
    status = "N/E"
    raster_used: str | None = None

    mineral_ok = mineral_supports_raster(mineral)
    if fav_path is not None and mineral_ok:
        try:
            grid = load_geogrid(fav_path)
            hit = query_favorability(grid, latitude=lat, longitude=lon, commodity="cu_co")
            in_bounds = hit.in_bounds
            info = classify_score(hit.score if in_bounds else None, in_bounds=in_bounds)
            # classify_score returns None for OOB — keep None (N/E), never coerce to 0
            if in_bounds and hit.score is not None and info.get("score_pct") is not None:
                prospectivity_pct = float(info["score_pct"])  # type: ignore[arg-type]
                level = _level_from_score(float(hit.score))
                status = "evaluated"
                raster_used = str(fav_path)
                model_used = f"{model} (raster {fav_path.name})"
            else:
                level = NE_LABEL
                status = "N/E"
                prospectivity_pct = None
                model_used = f"{model} (hors emprise pilote Kolwezi)"
        except Exception as exc:
            level = NE_LABEL
            status = "N/E"
            prospectivity_pct = None
            model_used = f"Erreur lecture raster : {exc}"
    else:
        level = NE_LABEL
        status = "N/E"
        prospectivity_pct = None
        if fav_path is None:
            model_used = "aucun raster"
        else:
            model_used = f"pas de raster pour « {mineral} » (pilote = Cu-Co Kolwezi)"

    conf_report: ConfidenceReport = build_confidence_report(
        prospectivity_pct=prospectivity_pct,
        prospectivity_level=level,
        features=features,
        in_bounds=in_bounds and status == "evaluated",
    )

    ne_guidance = None
    if status == "N/E":
        ne_guidance = prospectivity_ne_recommendation(prov, mineral)

    return ProspectivityResult(
        country="RDC",
        province=prov,
        zone=zone if zone in ZONE_PRESETS else prov,
        mineral=mineral,
        latitude=lat,
        longitude=lon,
        metric_crs=crs.label,
        prospectivity_pct=prospectivity_pct,
        prospectivity_level=level if status == "evaluated" else NE_LABEL,
        model_confidence_pct=conf_report.model_confidence_pct if status == "evaluated" else conf_report.model_confidence_pct,
        available_layers=conf_report.available,
        missing_layers=conf_report.missing,
        evidence_stage=conf_report.evidence_stage if status == "evaluated" else "N/E — PAS DE RASTER",
        model_used=model_used,
        raster_path=raster_used,
        in_bounds=in_bounds,
        disclaimer=(
            conf_report.disclaimer
            if status == "evaluated"
            else NE_MESSAGE + " " + conf_report.disclaimer
        ),
        recommendation_hint=_recommendation(
            level, conf_report.model_confidence_pct, in_bounds, is_ne=(status == "N/E")
        ),
        status=status,
        ne_guidance=ne_guidance,
    )
