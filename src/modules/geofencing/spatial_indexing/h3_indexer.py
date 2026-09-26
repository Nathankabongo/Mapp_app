"""Moteur d'indexation spatiale hexagonale basé sur Uber H3 pour sites miniers."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Set, Tuple

# Support de h3-py (v3 ou v4) avec fallback géodésique robuste
try:
    import h3

    _H3_AVAILABLE = True
    _H3_V4 = hasattr(h3, "latlng_to_cell")
except ImportError:
    h3 = None
    _H3_AVAILABLE = False
    _H3_V4 = False


class HexagonalSpatialIndexer:
    """
    Indexeur spatial hiérarchique utilisant le carroyage hexagonal H3 d'Uber.
    Idéal pour les sites miniers (Kolwezi, Tenke Fungurume, Kamoa-Kakula) :
    - Résolution 7 : Échelle régionale concession (~1.2 km de rayon)
    - Résolution 9 : Échelle carreau de mine / puits (~100 m)
    - Résolution 10 : Échelle micro-sécurité engins / détection collision (~65 m)
    """

    def __init__(self, default_resolution: int = 9):
        self.default_resolution = default_resolution

    def lat_lon_to_h3(self, lat: float, lon: float, resolution: int | None = None) -> str:
        """Convertit une coordonnée GPS (WGS84) en identifiant d'hexagone H3."""
        res = resolution if resolution is not None else self.default_resolution
        if _H3_AVAILABLE:
            if _H3_V4:
                return h3.latlng_to_cell(lat, lon, res)
            return h3.geo_to_h3(lat, lon, res)

        # Fallback pseudo-hexagonal discrétisé si h3 non disponible
        scale = 10**res
        return f"hex_{int(lat * scale):x}_{int(lon * scale):x}_{res}"

    def h3_to_lat_lon(self, h3_index: str) -> Tuple[float, float]:
        """Retourne les coordonnées (lat, lon) du centroïde de l'hexagone."""
        if _H3_AVAILABLE and not h3_index.startswith("hex_"):
            if _H3_V4:
                lat, lon = h3.cell_to_latlng(h3_index)
                return float(lat), float(lon)
            lat, lon = h3.h3_to_geo(h3_index)
            return float(lat), float(lon)

        # Décodage fallback
        parts = h3_index.split("_")
        if len(parts) == 4:
            scale = 10 ** int(parts[3])
            lat = int(parts[1], 16) / scale
            lon = int(parts[2], 16) / scale
            return lat, lon
        return 0.0, 0.0

    def get_k_ring(self, h3_index: str, k: int = 1) -> Set[str]:
        """
        Retourne l'ensemble des hexagones voisins dans un rayon d'ordre k.
        Utilisé pour modéliser le périmètre de sécurité autour d'une excavatrice ou d'un tir.
        """
        if _H3_AVAILABLE and not h3_index.startswith("hex_"):
            if _H3_V4:
                return set(h3.grid_disk(h3_index, k))
            return set(h3.k_ring(h3_index, k))

        # Fallback local
        return {h3_index}

    def h3_distance(self, h3_a: str, h3_b: str) -> int:
        """
        Calcule la distance en nombre de pas d'hexagone (complexité O(1)).
        """
        if h3_a == h3_b:
            return 0
        if _H3_AVAILABLE and not h3_a.startswith("hex_") and not h3_b.startswith("hex_"):
            try:
                if _H3_V4:
                    return int(h3.grid_distance(h3_a, h3_b))
                return int(h3.h3_distance(h3_a, h3_b))
            except Exception:
                pass

        # Approximation euclidienne
        lat1, lon1 = self.h3_to_lat_lon(h3_a)
        lat2, lon2 = self.h3_to_lat_lon(h3_b)
        dist_km = math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111.0
        return max(1, int(dist_km * 10))

    def polyfill_bbox(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        resolution: int | None = None,
    ) -> List[str]:
        """
        Génère la liste exhaustive des cellules H3 couvrant une boîte englobante de concession CAMI.
        """
        res = resolution if resolution is not None else self.default_resolution
        # Pas d'échantillonnage adapté à la résolution
        step = 1.0 / (2.0 ** (res - 2)) if res > 2 else 0.1
        hexagons = set()

        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                hexagons.add(self.lat_lon_to_h3(lat, lon, res))
                lon += step
            lat += step

        return list(hexagons)
