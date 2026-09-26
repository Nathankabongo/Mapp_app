"""Adapters : normalisation vers le modèle de données commun."""

from __future__ import annotations

from typing import Any


def normalize_layer_record(raw: dict[str, Any], *, data_class: str, source: str) -> dict[str, Any]:
    """Normalise un enregistrement vers le modèle commun Compass."""
    return {
        "id": raw.get("id") or raw.get("numero") or raw.get("name"),
        "name": raw.get("name") or raw.get("nom") or "",
        "geometry": raw.get("geometry"),
        "properties": {k: v for k, v in raw.items() if k != "geometry"},
        "data_class": data_class,
        "source": source,
        "confidence": raw.get("confidence"),
    }
