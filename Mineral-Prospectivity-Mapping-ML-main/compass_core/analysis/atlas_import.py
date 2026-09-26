"""Import et validation de couches CAMI / GeoPackage externes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
import pandas as pd

from compass_core.analysis.atlas_catalog import ATLAS_DIR, MineralLayerMeta, load_catalog

# Mapping des noms de champs CAMI / QGIS vers le schéma interne
CAMI_FIELD_ALIASES: dict[str, list[str]] = {
    "name": ["name", "nom", "site", "deposit", "gisement", "Name", "NOM"],
    "commodity": ["commodity", "minerai", "mineral", "commodite", "type_minerai"],
    "province": ["province", "Province", "PROVINCE", "admin1"],
    "status": ["status", "statut", "Statut", "permit_status", "etat"],
    "deposit_type": ["deposit_type", "type", "type_gisement", "geology_type"],
    "geological_formation": ["formation", "geological_formation", "lithologie", "geologie"],
    "cami_ref": ["cami_ref", "permis", "numero_permis", "ref_cami", "id"],
    "Value": ["Value", "value", "presence", "classe"],
}

REQUIRED_AFTER_IMPORT = ("name", "commodity")


@dataclass
class ImportReport:
    """Rapport d'import d'une couche atlas."""

    success: bool
    source_path: Path
    output_path: Path | None
    feature_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    field_mapping: dict[str, str] = field(default_factory=dict)


def _resolve_column(columns: list[str], canonical: str) -> str | None:
    lower_map = {col.lower(): col for col in columns}
    for alias in CAMI_FIELD_ALIASES.get(canonical, [canonical]):
        if alias in columns:
            return alias
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    return None


def normalize_gdf(gdf: gpd.GeoDataFrame, *, commodity: str) -> tuple[gpd.GeoDataFrame, dict[str, str]]:
    """Normalise un GeoDataFrame vers le schéma atlas interne."""
    mapping: dict[str, str] = {}
    normalized = gdf.copy()

    for canonical in list(CAMI_FIELD_ALIASES.keys()):
        source_col = _resolve_column(list(normalized.columns), canonical)
        if source_col and source_col != canonical:
            normalized[canonical] = normalized[source_col]
            mapping[canonical] = source_col
        elif source_col == canonical:
            mapping[canonical] = canonical

    if "commodity" not in normalized.columns:
        normalized["commodity"] = commodity
        mapping["commodity"] = "(défaut)"

    if "name" not in normalized.columns:
        normalized["name"] = [f"{commodity}_{i}" for i in range(len(normalized))]
        mapping["name"] = "(généré)"

    if "Value" not in normalized.columns:
        normalized["Value"] = 1

    if "source" not in normalized.columns:
        normalized["source"] = "import_cami"

    if normalized.crs is None:
        normalized = normalized.set_crs("EPSG:4326")
    elif normalized.crs.to_epsg() != 4326:
        normalized = normalized.to_crs(epsg=4326)

    return normalized, mapping


def validate_layer_gdf(gdf: gpd.GeoDataFrame) -> list[str]:
    """Valide un GeoDataFrame importé."""
    errors: list[str] = []
    if gdf.empty:
        errors.append("Couche vide.")
    if gdf.geometry.isnull().any():
        errors.append("Géométries nulles détectées.")
    geom_types = set(gdf.geometry.geom_type.unique())
    allowed = {"Point", "MultiPoint", "Polygon", "MultiPolygon"}
    if not geom_types.issubset(allowed):
        errors.append(f"Types géométriques non supportés : {geom_types - allowed}")
    for field_name in REQUIRED_AFTER_IMPORT:
        if field_name not in gdf.columns:
            errors.append(f"Champ requis manquant : {field_name}")
    return errors


def import_cami_layer(
    source_path: str | Path,
    commodity: str,
    *,
    output_dir: Path = ATLAS_DIR,
    overwrite: bool = True,
) -> ImportReport:
    """
    Importe un GeoPackage CAMI / QGIS dans l'atlas.

    Mappe automatiquement les champs courants vers le schéma interne.
    """
    source = Path(source_path)
    if not source.exists():
        return ImportReport(
            success=False,
            source_path=source,
            output_path=None,
            errors=[f"Fichier introuvable : {source}"],
        )

    catalog = load_catalog()
    meta = catalog.layers.get(commodity)
    if meta is None:
        return ImportReport(
            success=False,
            source_path=source,
            output_path=None,
            errors=[f"Commodité inconnue : {commodity}. Codes : {list(catalog.layers)}"],
        )

    try:
        gdf = gpd.read_file(source)
    except Exception as exc:
        return ImportReport(
            success=False,
            source_path=source,
            output_path=None,
            errors=[f"Lecture échouée : {exc}"],
        )

    normalized, mapping = normalize_gdf(gdf, commodity=commodity)
    errors = validate_layer_gdf(normalized)
    if errors:
        return ImportReport(
            success=False,
            source_path=source,
            output_path=None,
            errors=errors,
            field_mapping=mapping,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / meta.filename
    if output_path.exists() and not overwrite:
        return ImportReport(
            success=False,
            source_path=source,
            output_path=output_path,
            errors=[f"Fichier existant : {output_path} (utilisez overwrite=True)"],
            field_mapping=mapping,
        )

    keep_cols = [
        c
        for c in (
            "name",
            "commodity",
            "Value",
            "province",
            "status",
            "deposit_type",
            "geological_formation",
            "source",
            "cami_ref",
            "geometry",
        )
        if c in normalized.columns
    ]
    normalized[keep_cols].to_file(output_path, driver="GPKG")

    warnings: list[str] = []
    if "province" not in normalized.columns:
        warnings.append("Province non renseignée — filtrage provincial indisponible.")

    return ImportReport(
        success=True,
        source_path=source,
        output_path=output_path,
        feature_count=len(normalized),
        warnings=warnings,
        field_mapping=mapping,
    )


def layer_statistics(gdf: gpd.GeoDataFrame) -> dict[str, int | dict]:
    """Calcule des statistiques sur une couche."""
    stats: dict[str, int | dict] = {"total": len(gdf)}
    if "province" in gdf.columns:
        stats["by_province"] = gdf["province"].value_counts().to_dict()
    if "status" in gdf.columns:
        stats["by_status"] = gdf["status"].value_counts().to_dict()
    if "deposit_type" in gdf.columns:
        stats["by_type"] = gdf["deposit_type"].value_counts().to_dict()
    if "Value" in gdf.columns:
        stats["positive"] = int((gdf["Value"] == 1).sum())
        stats["negative"] = int((gdf["Value"] == 0).sum())
    return stats


def export_layer_table(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Exporte un tableau lisible (sans géométrie) pour l'interface."""
    cols = [
        c
        for c in (
            "name",
            "commodity",
            "province",
            "status",
            "deposit_type",
            "geological_formation",
            "Value",
            "source",
            "cami_ref",
        )
        if c in gdf.columns
    ]
    df = gdf[cols].copy()
    if "geometry" in gdf.columns:
        wgs = gdf.to_crs(epsg=4326)
        df["latitude"] = wgs.geometry.y
        df["longitude"] = wgs.geometry.x
    return df
