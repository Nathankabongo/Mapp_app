"""Proximite sites / cadastre / atlas."""

from __future__ import annotations

from compass_core.analysis.mineral_layers import find_nearby_deposits
from compass_core.constants import UNAVAILABLE
from compass_core.io.cadastral import load_cadastral_layer
from compass_core.spatial.distance import nearest_feature_km


def proximity_summary(latitude: float, longitude: float, *, radius_km: float = 25.0) -> dict:
    deposits = find_nearby_deposits(latitude, longitude, radius_km=radius_km)
    nearest_site = deposits[0] if deposits else None
    cadastre = load_cadastral_layer()
    dist_c, num = nearest_feature_km(
        latitude, longitude, cadastre, name_field="numero_permis"
    )
    return {
        "nearest_site_name": nearest_site.name if nearest_site else UNAVAILABLE,
        "nearest_site_km": nearest_site.distance_km if nearest_site else None,
        "nearest_site_commodity": nearest_site.label if nearest_site else UNAVAILABLE,
        "nearest_permit_km": dist_c,
        "nearest_permit_id": num or UNAVAILABLE,
        "nearby_count": len(deposits),
    }
