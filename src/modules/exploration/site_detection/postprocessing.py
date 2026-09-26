"""Post-traitement morphologique et vectorisation des détections de sites miniers."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_closing, binary_opening, label


def filter_and_polygonize_sites(
    mining_mask: np.ndarray,
    min_pixels: int = 4,
    pixel_size_m: float = 10.0,  # Résolution Sentinel-2
    origin_lon: float = 25.40,
    origin_lat: float = -10.80,
    deg_per_pixel: float = 0.0001,
) -> list[dict]:
    """
    Nettoie le masque par opérations morphologiques et extrait les clusters de puits miniers.
    Retourne une liste de polygones au format GeoJSON avec attributs statistiques.
    """
    # 1. Nettoyage morphologique : fermer les petits trous et éliminer le bruit isolé
    structure = np.ones((3, 3), dtype=bool)
    opened = binary_opening(mining_mask, structure=structure)
    cleaned = binary_closing(opened, structure=structure)

    # 2. Labellisation des composantes connexes
    labeled_array, num_features = label(cleaned, structure=structure)

    detected_features = []
    for feat_id in range(1, num_features + 1):
        indices = np.argwhere(labeled_array == feat_id)
        if len(indices) < min_pixels:
            continue

        r_coords = indices[:, 0]
        c_coords = indices[:, 1]

        min_r, max_r = int(np.min(r_coords)), int(np.max(r_coords))
        min_c, max_c = int(np.min(c_coords)), int(np.max(c_coords))

        centroid_r = float(np.mean(r_coords))
        centroid_c = float(np.mean(c_coords))

        # Conversion en coordonnées géographiques
        centroid_lon = origin_lon + centroid_c * deg_per_pixel
        centroid_lat = origin_lat - centroid_r * deg_per_pixel

        area_m2 = len(indices) * (pixel_size_m**2)
        area_ha = area_m2 / 10000.0

        bbox_geojson = [
            origin_lon + min_c * deg_per_pixel,
            origin_lat - max_r * deg_per_pixel,
            origin_lon + max_c * deg_per_pixel,
            origin_lat - min_r * deg_per_pixel,
        ]

        detected_features.append({
            "type": "Feature",
            "properties": {
                "site_id": f"ASM-DETECT-{feat_id:04d}",
                "pixel_count": int(len(indices)),
                "area_hectares": round(area_ha, 3),
                "confidence_score": round(min(1.0, 0.6 + 0.4 * (len(indices) / 50.0)), 2),
                "centroid": [round(centroid_lon, 5), round(centroid_lat, 5)],
            },
            "bbox": bbox_geojson,
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [bbox_geojson[0], bbox_geojson[1]],
                    [bbox_geojson[2], bbox_geojson[1]],
                    [bbox_geojson[2], bbox_geojson[3]],
                    [bbox_geojson[0], bbox_geojson[3]],
                    [bbox_geojson[0], bbox_geojson[1]],
                ]],
            },
        })

    return detected_features
