"""Landsat — connecteur."""

from __future__ import annotations

from compass_core.api.connectors import ConnectorResult


def probe_landsat() -> ConnectorResult:
    return ConnectorResult(
        False,
        "À CONFIGURER",
        "Landsat : accès EarthExplorer / M2M à configurer. Aucun téléchargement silencieux.",
        data_class="observation",
    )
