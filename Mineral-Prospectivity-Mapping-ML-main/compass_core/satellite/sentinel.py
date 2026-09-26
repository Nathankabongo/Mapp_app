"""Sentinel — connecteur (pas de téléchargement automatique)."""

from __future__ import annotations

from compass_core.api.connectors import ConnectorResult


def probe_sentinel2() -> ConnectorResult:
    return ConnectorResult(
        False,
        "À CONFIGURER",
        "Sentinel-2 : credentials Copernicus requis. Aucune scène téléchargée silencieusement.",
        data_class="observation",
    )
