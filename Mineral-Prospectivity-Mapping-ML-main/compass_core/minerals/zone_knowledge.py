"""Knowledge base Minerai × Zone — RDC (présence ≠ prospectivité)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from compass_core.analysis.mineral_layers import load_all_layers
from compass_core.analysis.site_evaluation import resolve_favorability_path
from compass_core.gis.layers import inventory_layers
from compass_core.io.data_sources import load_regions
from compass_core.minerals.profiles import get_profile, mineral_supports_raster

ZONE_MINERALS_PATH = Path("config/zone_minerals.json")

# Atlas layer codes ↔ minerai
ATLAS_MINERAL_MAP: dict[str, list[str]] = {
    "cu_co": ["cuivre", "cobalt"],
    "li": ["lithium"],
    "au": ["or"],
    "coltan": ["coltan", "tantale", "étain", "tungstène", "niobium"],
    "diamond": ["diamant"],
}


@dataclass
class ZoneMineralInfo:
    mineral: str
    evidence_level: str  # documented | limited | none
    flags: list[str] = field(default_factory=list)
    deposit_types: list[str] = field(default_factory=list)
    notes: str = ""
    occurrence_count: int | None = None
    why: list[str] = field(default_factory=list)
    prospectivity_available: bool = False
    badges: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ZoneFactSheet:
    province: str
    basin: str
    latitude: float
    longitude: float
    minerals: list[dict] = field(default_factory=list)
    occurrence_totals: dict = field(default_factory=dict)
    data_coverage: dict = field(default_factory=dict)
    pilot_note: str = ""
    disclaimer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=1)
def _load_kb(path: str | None = None) -> dict:
    p = Path(path) if path else ZONE_MINERALS_PATH
    if not p.exists():
        return {"provinces": {}, "localities": {}, "pilot_prospectivity": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def clear_kb_cache() -> None:
    _load_kb.cache_clear()


def normalize_province_name(name: str) -> str:
    """Harmonise alias (Kasaï Oriental → Kasaï-Oriental, etc.)."""
    raw = (name or "").strip()
    if not raw or raw in {"RDC", "Toute la RDC"}:
        return raw
    regions = load_regions()
    aliases = regions.get("aliases") or {}
    if raw in aliases:
        return aliases[raw]
    # reverse / fuzzy
    for alias, canon in aliases.items():
        if raw.lower() == alias.lower() or raw.lower() == canon.lower():
            return canon
    # match existing province list
    for p in regions.get("provinces", []):
        if p["name"].lower() == raw.lower():
            return p["name"]
    return raw


def list_all_provinces() -> list[str]:
    regions = load_regions()
    return sorted({normalize_province_name(p["name"]) for p in regions.get("provinces", [])})


def province_center(province: str) -> tuple[float, float]:
    regions = load_regions()
    name = normalize_province_name(province)
    for p in regions.get("provinces", []):
        if normalize_province_name(p["name"]) == name:
            if "center" in p:
                return float(p["center"][0]), float(p["center"][1])
            bbox = p["bbox"]
            return (bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2
    default = regions.get("map_default", {})
    return float(default.get("latitude", -4.0375)), float(default.get("longitude", 21.7587))


def list_localities(*, province: str | None = None) -> list[dict]:
    kb = _load_kb()
    out = []
    for name, meta in (kb.get("localities") or {}).items():
        if province and normalize_province_name(meta.get("province", "")) != normalize_province_name(province):
            continue
        out.append({"name": name, **meta})
    return sorted(out, key=lambda x: x["name"])


def _count_atlas_occurrences(province: str, mineral: str) -> int | None:
    """Compte les points atlas dans la province pour un minerai — None si couche absente."""
    profile = get_profile(mineral)
    layer_code = profile.atlas_layer if profile else None
    # fallback mappings
    if not layer_code:
        for code, minerals in ATLAS_MINERAL_MAP.items():
            if mineral.lower() in minerals:
                layer_code = code
                break
    if not layer_code:
        return None
    try:
        layers = load_all_layers(commodities=[layer_code])
    except Exception:
        return None
    gdf = layers.get(layer_code)
    if gdf is None or gdf.empty:
        return 0
    name = normalize_province_name(province)
    if "province" not in gdf.columns:
        return int(len(gdf))
    # match with aliases
    def _match(val: str) -> bool:
        return normalize_province_name(str(val)) == name

    subset = gdf[gdf["province"].astype(str).map(_match)]
    return int(len(subset))


def _badges_for(flags: list[str], evidence: str, prosp_ok: bool) -> list[str]:
    badges = []
    if "occurrences" in flags:
        badges.append("✓ Occurrences documentées")
    if "geology_context" in flags:
        badges.append("✓ Contexte géologique connu")
    if "pilot_raster" in flags and prosp_ok:
        badges.append("✓ Raster prospectivité pilote")
    if evidence == "limited":
        badges.append("⚠ Occurrences / données limitées")
    if not prosp_ok:
        badges.append("⚠ Pas de carte raster de prospectivité")
    if "associated_cu" in flags:
        badges.append("✓ Associé systèmes Cu-Co")
    return badges


def minerals_for_zone(province: str) -> list[ZoneMineralInfo]:
    """Minerais documentés / pertinents pour une province — liste contextuelle."""
    kb = _load_kb()
    name = normalize_province_name(province)
    block = (kb.get("provinces") or {}).get(name) or {}
    pilot = kb.get("pilot_prospectivity") or {}
    pilot_minerals = {m.lower() for m in (pilot.get("minerals") or [])}
    pilot_provinces = {normalize_province_name(p) for p in (pilot.get("provinces") or [])}

    raw_list = list(block.get("minerals") or [])
    out: list[ZoneMineralInfo] = []
    for item in raw_list:
        mineral = str(item.get("mineral", ""))
        flags = list(item.get("flags") or [])
        evidence = str(item.get("evidence_level", "limited"))
        prosp_ok = (
            mineral.lower() in pilot_minerals
            and name in pilot_provinces
            and mineral_supports_raster(mineral)
            and resolve_favorability_path() is not None
        )
        # Si hors Lualaba, même cuivre n'a pas le raster pilote sur toute la province
        # (emprise Kolwezi seulement) — prosp_ok reste True seulement si on pourra
        # évaluer in_bounds plus tard ; ici on signale la *possibilité* de raster.
        if mineral.lower() in pilot_minerals and resolve_favorability_path() is not None:
            if "pilot_raster" not in flags and name in pilot_provinces:
                flags = [*flags, "pilot_raster"]
            # Haut-Katanga cuivre : occurrences oui, raster Kolwezi souvent hors emprise
            if name not in pilot_provinces:
                prosp_ok = False
            else:
                prosp_ok = True  # possibilité ; N/E si hors pixels

        count = _count_atlas_occurrences(name, mineral)
        why = []
        if evidence == "documented":
            why.append("Documenté dans la base Minerai × Zone")
        elif evidence == "limited":
            why.append("Mentions limitées — à confirmer avec données locales")
        if item.get("notes"):
            why.append(str(item["notes"]))
        if count:
            why.append(f"{count} occurrence(s) atlas dans la province")
        elif count == 0:
            why.append("Aucune occurrence atlas filtrée pour cette province")

        out.append(
            ZoneMineralInfo(
                mineral=mineral,
                evidence_level=evidence,
                flags=flags,
                deposit_types=list(item.get("deposit_types") or []),
                notes=str(item.get("notes") or ""),
                occurrence_count=count,
                why=why,
                prospectivity_available=prosp_ok,
                badges=_badges_for(flags, evidence, prosp_ok),
            )
        )
    return out


def default_mineral_for_zone(province: str) -> str | None:
    minerals = minerals_for_zone(province)
    if not minerals:
        return None
    documented = [m for m in minerals if m.evidence_level == "documented"]
    pool = documented or minerals

    def _rank(m: ZoneMineralInfo) -> tuple:
        # Priorité : raster pilote > occurrences > cuivre (substance tête de file Copperbelt)
        pilot = 1 if m.prospectivity_available or "pilot_raster" in m.flags else 0
        occ = m.occurrence_count or 0
        prefer_cu = 1 if m.mineral == "cuivre" else 0
        prefer_primary = 1 if m.mineral in {"cuivre", "or", "diamant", "lithium"} else 0
        return (-pilot, -prefer_primary, -occ, -prefer_cu, m.mineral)

    pool = sorted(pool, key=_rank)
    return pool[0].mineral


def recommended_model_for(
    *,
    province: str,
    mineral: str,
    locality: str | None = None,
) -> dict:
    """
    Modèle recommandé pour le couple Zone × Minerai.

    - Emprise pilote Cu-Co (Lualaba / localités Kolwezi…) + cuivre/cobalt → WoE (raster disponible)
    - Sinon → aucun modèle entraîné pour cette emprise (N/E)
    """
    from compass_core.prospectivity.models import MODEL_CATALOG

    name = normalize_province_name(province)
    kb = _load_kb()
    pilot = kb.get("pilot_prospectivity") or {}
    pilot_minerals = {m.lower() for m in (pilot.get("minerals") or [])}
    pilot_provinces = {normalize_province_name(p) for p in (pilot.get("provinces") or [])}
    pilot_locs = {str(x) for x in (pilot.get("localities") or [])}

    has_raster = resolve_favorability_path() is not None and mineral_supports_raster(mineral)
    in_pilot_province = name in pilot_provinces and mineral.lower() in pilot_minerals
    in_pilot_locality = bool(locality) and locality in pilot_locs and mineral.lower() in pilot_minerals

    available = [m for m in MODEL_CATALOG if m.get("status") == "disponible"]
    codes = [m["code"] for m in available] or ["woe"]

    if has_raster and (in_pilot_province or in_pilot_locality):
        return {
            "code": "woe",
            "label": "Weights of Evidence (WoE)",
            "status": "disponible",
            "reason": (
                "Modèle pilote Cu-Co Kolwezi — raster de prospectivité disponible. "
                "Alternatives : " + ", ".join(codes)
            ),
            "alternatives": codes,
            "prospectivity_ready": True,
        }

    return {
        "code": None,
        "label": "Aucun modèle pour cette emprise",
        "status": "N/E",
        "reason": (
            f"Minerai « {mineral} » documenté ou sélectionné pour {name}, "
            "mais aucun modèle / raster de prospectivité n'est encore entraîné pour cette zone. "
            "Construire un modèle après acquisition des données."
        ),
        "alternatives": codes,
        "prospectivity_ready": False,
    }


def resolve_zone_defaults(
    *,
    province: str,
    locality: str | None = None,
) -> dict:
    """
    Après sélection d'une zone : minerai cible à exploiter + modèle associé.
    """
    name = normalize_province_name(province)
    mineral = None
    lat, lon = province_center(name)
    zone_label = name

    if locality and locality not in {"", "(Centroïde province)"}:
        locs = {L["name"]: L for L in list_localities(province=name)}
        # aussi chercher toutes localités si hors filtre
        if locality not in locs:
            locs = {L["name"]: L for L in list_localities()}
        meta = locs.get(locality)
        if meta:
            lat, lon = float(meta["lat"]), float(meta["lon"])
            zone_label = locality
            mineral = meta.get("mineral_default")

    if not mineral:
        mineral = default_mineral_for_zone(name)

    minerals = minerals_for_zone(name)
    model = recommended_model_for(
        province=name,
        mineral=mineral or "cuivre",
        locality=locality if locality and locality != "(Centroïde province)" else None,
    )
    selected = next((m for m in minerals if m.mineral == mineral), None)

    return {
        "province": name,
        "zone": zone_label,
        "latitude": lat,
        "longitude": lon,
        "mineral": mineral,
        "minerals_available": [m.to_dict() for m in minerals],
        "mineral_info": selected.to_dict() if selected else None,
        "model": model,
    }


def data_coverage_for_zone(province: str, *, latitude: float, longitude: float, mineral: str) -> dict:
    """Indicateurs de couverture 0–100 — honnêtes, basés sur inventaire local."""
    layers = {L.id: L for L in inventory_layers()}
    minerals = {m.mineral: m for m in minerals_for_zone(province)}
    info = minerals.get(mineral)

    def _pct(status: str, *, demo_as: int = 40) -> int:
        if status == "available":
            return 100
        if status == "demo":
            return demo_as
        if status == "remote":
            return 70
        if status == "missing":
            return 0
        return 10

    geology = 80 if info and "geology_context" in (info.flags or []) else _pct(layers.get("geology").status if layers.get("geology") else "missing")
    if info and (info.occurrence_count or 0) > 0:
        geology = max(geology, 70)

    satellite = _pct(layers.get("imagery").status if layers.get("imagery") else "remote")
    geochem = _pct(layers.get("geochem").status if layers.get("geochem") else "missing")
    geophy = _pct(layers.get("geophysics").status if layers.get("geophysics") else "missing", demo_as=35)
    forages = 20 if Path("data/rdc/demo/drillholes/collars.csv").exists() else 0

    # Prospectivité : 100 seulement si raster + minerai supporté + (sera affiné in_bounds)
    prosp = 0
    fav = resolve_favorability_path()
    if fav and mineral_supports_raster(mineral):
        prosp = 10  # modèle existe nationalement pour Cu-Co, emprise limitée
        pilot = (_load_kb().get("pilot_prospectivity") or {})
        if normalize_province_name(province) in {
            normalize_province_name(p) for p in (pilot.get("provinces") or [])
        } and mineral.lower() in {m.lower() for m in (pilot.get("minerals") or [])}:
            prosp = 55  # province pilote — encore N/E hors pixels Kolwezi

    return {
        "geology": {"pct": geology, "label": "Géologie / occurrences"},
        "satellite": {"pct": satellite, "label": "Satellite (fonds)"},
        "geochemistry": {"pct": geochem, "label": "Géochimie"},
        "geophysics": {"pct": geophy, "label": "Géophysique"},
        "drillholes": {"pct": forages, "label": "Forages"},
        "prospectivity": {"pct": prosp, "label": "Prospectivité raster"},
    }


def prospectivity_ne_recommendation(province: str, mineral: str) -> dict:
    """Quand prospectivité = N/E : recommandations d'acquisition (utiles)."""
    info_list = minerals_for_zone(province)
    info = next((m for m in info_list if m.mineral == mineral), None)
    documented = info is not None and info.evidence_level in {"documented", "limited"}
    steps = [
        "Analyser / importer les données géologiques de la zone",
        "Rechercher les signatures satellitaires (altération, structures)",
        "Intégrer la géochimie disponible",
        "Intégrer la géophysique disponible",
        "Construire un modèle de prospectivité pour ce couple Minerai × Zone",
    ]
    return {
        "prospectivity": "N/E",
        "meaning": (
            "Non évalué — données de prospectivité indisponibles pour cette emprise / ce minerai. "
            "Ce n'est pas un score de favorabilité nulle."
        ),
        "mineral_documented": documented,
        "evidence_level": info.evidence_level if info else "none",
        "why_ne": (
            "Occurrences ou contexte connus, mais aucun modèle raster de prospectivité "
            "disponible pour cette zone et ce minerai."
            if documented
            else "Ni modèle raster, ni base documentaire suffisante pour ce couple zone/minerai."
        ),
        "recommendations": steps if documented else [
            "Documenter les occurrences minérales de la province",
            *steps,
        ],
        "pilot_available_elsewhere": (
            "Un raster Cu-Co pilote existe pour l'emprise Kolwezi (Lualaba) uniquement."
        ),
    }


def zone_fact_sheet(province: str, *, latitude: float | None = None, longitude: float | None = None) -> ZoneFactSheet:
    name = normalize_province_name(province)
    lat, lon = (latitude, longitude) if latitude is not None and longitude is not None else province_center(name)
    kb = _load_kb()
    block = (kb.get("provinces") or {}).get(name) or {}
    minerals = minerals_for_zone(name)
    totals = {m.mineral: m.occurrence_count for m in minerals if m.occurrence_count is not None}
    default_m = default_mineral_for_zone(name) or "cuivre"
    coverage = data_coverage_for_zone(name, latitude=lat, longitude=lon, mineral=default_m)
    pilot = kb.get("pilot_prospectivity") or {}
    return ZoneFactSheet(
        province=name,
        basin=str(block.get("basin") or "—"),
        latitude=lat,
        longitude=lon,
        minerals=[m.to_dict() for m in minerals],
        occurrence_totals=totals,
        data_coverage=coverage,
        pilot_note=str(pilot.get("note") or ""),
        disclaimer=str(kb.get("disclaimer") or ""),
    )


def build_campaign_zone_context(
    province: str,
    mineral: str,
    *,
    latitude: float,
    longitude: float,
) -> dict:
    """Contexte complet pour la campagne nationale."""
    sheet = zone_fact_sheet(province, latitude=latitude, longitude=longitude)
    minerals = minerals_for_zone(province)
    selected = next((m for m in minerals if m.mineral == mineral), None)
    coverage = data_coverage_for_zone(province, latitude=latitude, longitude=longitude, mineral=mineral)
    return {
        "province": normalize_province_name(province),
        "mineral": mineral,
        "fact_sheet": sheet.to_dict(),
        "selected_mineral": selected.to_dict() if selected else None,
        "available_minerals": [m.to_dict() for m in minerals],
        "data_coverage": coverage,
        "ne_guidance": prospectivity_ne_recommendation(province, mineral),
        "rule": (
            "Présence documentée ≠ prospectivité. "
            "Score numérique uniquement si raster évalué ; sinon N/E (jamais 0 artificiel)."
        ),
    }
