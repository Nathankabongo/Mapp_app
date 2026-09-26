"""Campagne d'exploration nationale RDC — Minerai × Zone × Données × Modèle."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from compass_core.exploration.diagnostic import diagnose_zone
from compass_core.exploration.ranking import rank_targets
from compass_core.exploration.targets import generate_targets
from compass_core.minerals.zone_knowledge import (
    build_campaign_zone_context,
    default_mineral_for_zone,
    normalize_province_name,
    province_center,
)
from compass_core.prospectivity.prediction import ZONE_PRESETS, run_prospectivity


@dataclass
class ExplorationCampaign:
    """Campagne d'exploration minière nationale (RDC)."""

    campaign_id: str
    country: str
    province: str
    zone: str
    mineral: str
    exploration_type: str
    latitude: float
    longitude: float
    created_at: str
    prospectivity: dict
    targets: list[dict] = field(default_factory=list)
    data_inventory: dict = field(default_factory=dict)
    diagnostic: dict = field(default_factory=dict)
    zone_context: dict = field(default_factory=dict)
    disclaimer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def inventory_for_zone(*, province: str, mineral: str, prosp: dict) -> dict:
    """Inventaire honnête des données disponibles pour la zone."""
    available = list(prosp.get("available_layers") or [])
    missing = list(prosp.get("missing_layers") or [])
    status = prosp.get("status", "N/E")
    return {
        "satellite": {
            "status": "PARTIEL",
            "items": ["Sentinel-1", "Sentinel-2", "Landsat"],
            "note": "Tuiles de fond disponibles ; scènes analysables absentes sans import.",
        },
        "geology": {
            "status": "PARTIEL" if any("Géologie" in a or "géologie" in a.lower() for a in available) else "LIMITÉ",
            "items": ["lithologie", "structures", "failles", "occurrences"],
        },
        "geophysics": {"status": "NON DISPONIBLE", "items": ["magnétique", "radiométrie", "gravimétrie", "EM"]},
        "geochemistry": {"status": "NON DISPONIBLE", "items": ["sols", "sédiments", "roches"]},
        "mining": {
            "status": "DÉMO / LOCAL",
            "items": ["occurrences atlas", "concessions locales (non CAMI vérifié)"],
        },
        "prospectivity_raster": {
            "status": "ÉVALUÉ" if status == "evaluated" else "N/E",
            "note": (
                "Raster pilote Cu-Co Kolwezi"
                if status == "evaluated"
                else "Aucun raster pour cette emprise / ce minerai"
            ),
        },
        "available_layers": available,
        "missing_layers": missing,
        "province": province,
        "mineral": mineral,
    }


def run_campaign(
    *,
    zone: str | None = None,
    province: str | None = None,
    mineral: str | None = None,
    model: str | None = None,
    exploration_type: str = "Régionale",
    latitude: float | None = None,
    longitude: float | None = None,
    max_targets: int = 10,
) -> ExplorationCampaign:
    """
    Pipeline national :
    Province/zone → minerais documentés → données → prospectivité (ou N/E) → cibles si évalué.
    """
    # Résoudre lat/lon
    if latitude is not None and longitude is not None:
        lat, lon = float(latitude), float(longitude)
        zone_label = zone or (province or "Personnalisée")
    elif zone and zone in ZONE_PRESETS:
        preset = ZONE_PRESETS[zone]
        lat, lon = float(preset["lat"]), float(preset["lon"])
        zone_label = zone
        province = province or preset.get("province")
    elif province:
        lat, lon = province_center(province)
        zone_label = zone or province
    else:
        # défaut national documenté : Lualaba / Kolwezi (pilote), pas une limitation produit
        lat, lon = province_center("Lualaba")
        zone_label = zone or "Kolwezi"
        province = province or "Lualaba"

    prov = normalize_province_name(province or "RDC")
    if not mineral:
        mineral = default_mineral_for_zone(prov) or "cuivre"

    model_code = model or "woe"
    prosp = run_prospectivity(
        zone=zone_label,
        mineral=mineral,
        latitude=lat,
        longitude=lon,
        province=prov,
        model=model_code,
    )
    # Cibles automatiques uniquement si prospectivité réellement évaluée
    if prosp.status == "evaluated" and prosp.prospectivity_pct is not None:
        targets = generate_targets(
            zone=zone_label,
            mineral=mineral,
            latitude=lat,
            longitude=lon,
            max_targets=max_targets,
            base_confidence=prosp.model_confidence_pct,
            available_layers=prosp.available_layers,
            missing_layers=prosp.missing_layers,
        )
        ranked = rank_targets(targets)
    else:
        ranked = []

    inv = inventory_for_zone(province=prosp.province, mineral=mineral, prosp=prosp.to_dict())
    diagnostic = diagnose_zone(zone=zone_label, mineral=mineral, latitude=lat, longitude=lon)
    zone_ctx = build_campaign_zone_context(prosp.province, mineral, latitude=lat, longitude=lon)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_zone = "".join(ch if ch.isalnum() else "-" for ch in zone_label)[:20].upper()

    return ExplorationCampaign(
        campaign_id=f"EXP-{safe_zone}-{mineral.upper()[:3]}-{stamp}",
        country="RDC",
        province=prosp.province,
        zone=zone_label,
        mineral=mineral,
        exploration_type=exploration_type,
        latitude=lat,
        longitude=lon,
        created_at=stamp,
        prospectivity=prosp.to_dict(),
        targets=[t.to_dict() for t in ranked],
        data_inventory=inv,
        diagnostic=diagnostic.to_dict(),
        zone_context=zone_ctx,
        disclaimer=(
            "Campagne nationale d'exploration minière en RDC. "
            "Présence documentée ≠ prospectivité. "
            "Score numérique uniquement sur emprise pilote Cu-Co Kolwezi ; sinon N/E (jamais 0 artificiel). "
            "Prédictions IA ≠ gisement confirmé. Aucune teneur inventée."
        ),
    )
