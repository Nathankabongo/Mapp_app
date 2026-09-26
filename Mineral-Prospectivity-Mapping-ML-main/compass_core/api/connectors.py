"""Connecteurs — interfaces uniquement (pas de téléchargement silencieux)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConnectorResult:
    ok: bool
    status: str
    message: str
    path: str | None = None
    data_class: str = "unavailable"


class BaseConnector(ABC):
    id: str
    name: str

    @abstractmethod
    def probe(self) -> ConnectorResult:
        """Vérifie disponibilité locale / credentials — ne télécharge pas."""


class LocalFileConnector(BaseConnector):
    def __init__(self, id: str, name: str, path: str, data_class: str = "imported"):
        self.id = id
        self.name = name
        self.path = path
        self.data_class = data_class

    def probe(self) -> ConnectorResult:
        p = Path(self.path)
        if p.exists():
            return ConnectorResult(True, "DISPONIBLE", f"Fichier local : {p}", str(p), self.data_class)
        return ConnectorResult(
            False,
            "NON DISPONIBLE",
            "Information non disponible dans les sources utilisées.",
            None,
            "unavailable",
        )


class CamiConnector(LocalFileConnector):
    """Import CAMI : CSV / GeoJSON / GPKG / SHP — jamais d'invention."""

    def __init__(self, path: str = "data/rdc/official/cami_permits.gpkg"):
        super().__init__("cami", "CAMI Data Connector", path, "official")

    def probe(self) -> ConnectorResult:
        official = Path(self.path)
        demo = Path("data/rdc/atlas/cadastre_permis.gpkg")
        if official.exists():
            return ConnectorResult(True, "CONNECTÉ", "Export CAMI officiel détecté", str(official), "official")
        if demo.exists():
            return ConnectorResult(
                False,
                "DÉMO",
                "Seule une couche de démonstration est présente — Concessions vérifiées = 0",
                str(demo),
                "demo",
            )
        return ConnectorResult(
            False,
            "NON DISPONIBLE",
            "Information non disponible dans les sources utilisées.",
            None,
            "unavailable",
        )


def default_connectors() -> list[BaseConnector]:
    return [
        CamiConnector(),
        LocalFileConnector(
            "kolwezi_stack",
            "Raster multiphysique Kolwezi",
            "data/rdc/kolwezi/stack_multiphysics.tif",
            "demo",
        ),
        LocalFileConnector(
            "favorability",
            "Raster prospectivité",
            "outputs/kolwezi_sample/kolwezi_woe_cu_co_favorability.npy",
            "prediction",
        ),
    ]


def probe_all() -> list[dict]:
    rows = []
    for c in default_connectors():
        r = c.probe()
        rows.append(
            {
                "id": c.id,
                "name": c.name,
                "ok": r.ok,
                "status": r.status,
                "message": r.message,
                "path": r.path,
                "data_class": r.data_class,
            }
        )
    return rows
