"""Diagnostic automatique d'une zone d'exploration — ce que l'on sait et ce qui manque."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from compass_core.analysis.mineral_layers import find_nearby_deposits, load_all_layers
from compass_core.analysis.site_evaluation import evaluate_site, resolve_favorability_path
from compass_core.constants import UNAVAILABLE
from compass_core.drillholes.store import drillhole_count, load_demo_drillholes
from compass_core.gis.layers import inventory_layers
from compass_core.io.cadastral import lookup_permit
from compass_core.mining.cami import cami_status
from compass_core.minerals.profiles import get_profile
from compass_core.prospectivity.prediction import ZONE_PRESETS, run_prospectivity
from compass_core.spatial.distance import haversine_km


@dataclass
class DomainStatus:
    name: str
    status: str  # DISPONIBLE | PARTIEL | DÉMO | NON DISPONIBLE
    counts: dict[str, int | str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    data_class: str = "unavailable"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ZoneDiagnostic:
    zone: str
    mineral: str
    province: str
    latitude: float
    longitude: float
    geology: DomainStatus
    geochemistry: DomainStatus
    geophysics: DomainStatus
    satellite: DomainStatus
    exploration_history: DomainStatus
    cadastre: DomainStatus
    prospectivity: dict
    gaps: list[str] = field(default_factory=list)
    available_summary: list[str] = field(default_factory=list)
    mineral_profile: dict | None = None
    disclaimer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _count_nearby_occurrences(lat: float, lon: float, mineral: str) -> tuple[int, str]:
    profile = get_profile(mineral)
    layer = profile.atlas_layer if profile else None
    try:
        all_layers = load_all_layers()
        if layer and layer in all_layers:
            layers = {layer: all_layers[layer]}
        else:
            layers = all_layers
        nearby = find_nearby_deposits(lat, lon, layers=layers, radius_km=50.0)
        return len(nearby), "historical" if nearby else "unavailable"
    except Exception:
        return 0, "unavailable"


def _count_drillholes_near(lat: float, lon: float, radius_km: float = 40.0) -> tuple[int, str]:
    holes = load_demo_drillholes()
    if not holes:
        return 0, "unavailable"
    n = 0
    for h in holes:
        try:
            d = haversine_km(lat, lon, float(h.collar.y), float(h.collar.x))
            if d <= radius_km:
                n += 1
        except Exception:
            continue
    return n, "demo"


def diagnose_zone(
    *,
    zone: str = "Kolwezi",
    mineral: str = "cuivre",
    latitude: float | None = None,
    longitude: float | None = None,
) -> ZoneDiagnostic:
    """
    Produit un diagnostic honnête : comptages réels quand les fichiers existent,
    sinon NON DISPONIBLE — jamais de valeurs inventées.
    """
    preset = ZONE_PRESETS.get(zone, ZONE_PRESETS["Kolwezi"])
    lat = float(latitude if latitude is not None else preset["lat"])
    lon = float(longitude if longitude is not None else preset["lon"])

    prosp = run_prospectivity(zone=zone, mineral=mineral, latitude=lat, longitude=lon)
    profile = get_profile(mineral)
    layers = inventory_layers()
    by_id = {L.id: L for L in layers}

    occ_n, occ_class = _count_nearby_occurrences(lat, lon, mineral)
    dh_n, dh_class = _count_drillholes_near(lat, lon)
    dh_info = drillhole_count()

    # Géologie — occurrences atlas + couches inventaire
    geo_layer = by_id.get("geology")
    geo_status = "NON DISPONIBLE"
    geo_class = "unavailable"
    geo_notes = []
    if geo_layer and geo_layer.status == "available":
        geo_status = "DISPONIBLE"
        geo_class = geo_layer.data_class
    elif occ_n > 0:
        geo_status = "PARTIEL"
        geo_class = "historical"
        geo_notes.append("Unités géologiques vectorielles absentes — occurrences atlas uniquement.")
    else:
        geo_notes.append("Aucune couche géologique locale pour cette zone.")

    geology = DomainStatus(
        name="GÉOLOGIE",
        status=geo_status,
        counts={
            "occurrences_rayon_50km": occ_n,
            "lithologies_favorables": (
                len(profile.favorable_lithologies) if profile else "Donnée indisponible"
            ),
            "unites_geologiques_fichier": (
                "présent" if geo_layer and geo_layer.status == "available" else "absent"
            ),
            "failles_fichier": "absent",
        },
        notes=geo_notes
        + (
            [f"Contexte profil : {profile.geological_context}"]
            if profile and profile.geological_context
            else []
        ),
        data_class=geo_class,
    )

    # Géochimie — jamais inventée
    geochemistry = DomainStatus(
        name="GÉOCHIMIE",
        status="NON DISPONIBLE",
        counts={
            "echantillons": "Donnée indisponible",
            "anomalies_Cu": "Donnée indisponible",
            "anomalies_Co": "Donnée indisponible",
        },
        notes=["Aucun jeu géochimique importé pour cette zone."],
        data_class="unavailable",
    )

    # Géophysique — stack Kolwezi démo si présent
    gphy = by_id.get("geophysics")
    if gphy and gphy.status in {"demo", "available"}:
        geophysics = DomainStatus(
            name="GÉOPHYSIQUE",
            status="DÉMO" if gphy.status == "demo" else "PARTIEL",
            counts={
                "stack_multiphysique": 1,
                "anomalies_magnetiques": "Donnée indisponible",
                "anomalies_gravimetriques": "Donnée indisponible",
            },
            notes=[
                gphy.note or "Stack multiphysique présent (démonstration).",
                "Anomalies individuelles non extraites automatiquement.",
            ],
            data_class=gphy.data_class,
        )
    else:
        geophysics = DomainStatus(
            name="GÉOPHYSIQUE",
            status="NON DISPONIBLE",
            counts={
                "anomalies_magnetiques": "Donnée indisponible",
                "anomalies_gravimetriques": "Donnée indisponible",
            },
            notes=["Aucune donnée géophysique disponible dans cette zone."],
            data_class="unavailable",
        )

    # Satellite
    satellite = DomainStatus(
        name="TÉLÉDÉTECTION",
        status="PARTIEL",
        counts={"tuiles_fond": 1, "scenes_analysees": 0, "indices_spectraux": "Donnée indisponible"},
        notes=[
            "Fonds ESRI/OSM disponibles.",
            "Scènes Sentinel/Landsat analysables : non importées.",
        ],
        data_class="observation",
    )

    # Historique exploration
    fav = resolve_favorability_path()
    exploration_history = DomainStatus(
        name="EXPLORATION HISTORIQUE",
        status="DÉMO" if dh_n or fav else "LIMITÉ",
        counts={
            "forages_proches": dh_n,
            "forages_total_demo": dh_info.get("count", 0),
            "occurrences": occ_n,
            "raster_prospectivite": 1 if fav else 0,
            "campagnes_documentees": "Donnée indisponible",
        },
        notes=[
            dh_info.get("message", ""),
            "Campagnes historiques structurées : non encore en base.",
        ],
        data_class=dh_class if dh_n else ("prediction" if fav else "unavailable"),
    )

    # Cadastre
    try:
        permit = lookup_permit(lat, lon)
        if isinstance(permit, dict):
            permit_txt = permit.get("status_label") or permit.get("numero") or UNAVAILABLE
        else:
            permit_txt = str(permit)
    except Exception:
        permit_txt = UNAVAILABLE
    cami = cami_status()
    cadastre = DomainStatus(
        name="CADASTRE",
        status="DÉMO" if cami.get("verified_count", 0) == 0 else "PARTIEL",
        counts={
            "concessions_cami_verifiees": int(cami.get("verified_count", 0)),
            "lookup_point": 1 if permit_txt and permit_txt != UNAVAILABLE else 0,
        },
        notes=[
            f"Lookup local : {permit_txt}",
            cami.get("message", "CAMI officiel non chargé."),
        ],
        data_class="demo" if cami.get("verified_count", 0) == 0 else "official",
    )

    # Lacunes
    gaps: list[str] = []
    available: list[str] = []

    if geology.status in {"DISPONIBLE", "PARTIEL", "DÉMO"}:
        available.append(f"Géologie / occurrences : {geology.status}")
    else:
        gaps.append("Aucune donnée géologique vectorielle pour la zone")

    if occ_n == 0:
        gaps.append("Aucune occurrence minérale dans un rayon de 50 km (atlas local)")
    else:
        available.append(f"{occ_n} occurrence(s) atlas ≤ 50 km")

    if geochemistry.status == "NON DISPONIBLE":
        gaps.append("Faible / nulle densité géochimique — aucun échantillon importé")

    if geophysics.status == "NON DISPONIBLE":
        gaps.append("Données géophysiques absentes")
    elif geophysics.status == "DÉMO":
        gaps.append("Géophysique de démonstration uniquement — ne pas traiter comme lever réel")
        available.append("Stack multiphysique Kolwezi (DÉMO)")

    if dh_n == 0:
        gaps.append("Aucun forage à proximité (ou forages DEMO hors zone)")
    else:
        available.append(f"{dh_n} forage(s) DEMO à proximité")
        gaps.append("Forages disponibles = démonstration pédagogique (pas d'assays)")

    if not fav:
        gaps.append("Pas de raster de prospectivité pour ce minerai / cette emprise")
    else:
        available.append(f"Raster prospectivité : {Path(fav).name}")

    if satellite.counts.get("scenes_analysees", 0) == 0:
        gaps.append("Aucune scène satellitaire analysée (indices / altération indisponibles)")

    if int(cami.get("verified_count", 0)) == 0:
        gaps.append("Cadastre CAMI officiel non vérifié — contraintes permis incertaines")

    if prosp.model_confidence_pct < 50:
        gaps.append(f"Forte incertitude modèle (confiance {prosp.model_confidence_pct:.0f} %)")

    try:
        site = evaluate_site(lat, lon)
        if getattr(site.terrain, "risk_level", "") == "inconnu":
            gaps.append("Relief / pente non évalués (DEM insuffisant hors emprise)")
    except Exception:
        gaps.append("Évaluation terrain indisponible")

    return ZoneDiagnostic(
        zone=zone,
        mineral=mineral,
        province=prosp.province,
        latitude=lat,
        longitude=lon,
        geology=geology,
        geochemistry=geochemistry,
        geophysics=geophysics,
        satellite=satellite,
        exploration_history=exploration_history,
        cadastre=cadastre,
        prospectivity=prosp.to_dict(),
        gaps=gaps,
        available_summary=available,
        mineral_profile=profile.to_dict() if profile else None,
        disclaimer=(
            "Diagnostic d'aide à l'exploration. "
            "Les comptages absents sont marqués « Donnée indisponible » — aucune invention. "
            "Prédiction IA ≠ gisement confirmé."
        ),
    )
