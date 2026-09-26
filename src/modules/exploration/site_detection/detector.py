"""Détecteur automatisé de sites miniers artisanaux et excavations par télédétection multispectrale."""

from __future__ import annotations

import numpy as np


class MiningSiteDetector:
    """
    Algorithme inspiré des travaux DataKind / Global Witness pour la détection automatisée
    des empreintes minières artisanales (puits, déblais, bassins de décantation) via Sentinel-2.
    """

    def __init__(
        self,
        bsi_threshold: float = 0.15,
        ndvi_max_threshold: float = 0.25,
        min_excavation_score: float = 0.35,
    ):
        self.bsi_threshold = bsi_threshold
        self.ndvi_max_threshold = ndvi_max_threshold
        self.min_excavation_score = min_excavation_score

    def compute_indices(
        self,
        blue: np.ndarray,
        green: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir1: np.ndarray,
    ) -> dict[str, np.ndarray]:
        """
        Calcule les indices spectraux discriminants pour les excavations et rejets miniers.
        """
        eps = 1e-6
        # NDVI : Perte de couvert végétal
        ndvi = (nir - red) / (nir + red + eps)

        # NDWI : Eau turbide / bassins miniers
        ndwi = (green - nir) / (green + nir + eps)

        # BSI (Bare Soil Index) : Sol nu et roches décapées
        bsi_num = (red + swir1) - (nir + blue)
        bsi_den = (red + swir1) + (nir + blue) + eps
        bsi = bsi_num / bsi_den

        # Score composite d'excavation minière
        # Fort sol nu (BSI élevé) + Absence de végétation (NDVI bas) + présence d'eau/boues
        excavation_score = (bsi - ndvi) * 0.7 + np.clip(ndwi, 0, 1) * 0.3

        return {
            "ndvi": np.clip(ndvi, -1.0, 1.0),
            "ndwi": np.clip(ndwi, -1.0, 1.0),
            "bsi": np.clip(bsi, -1.0, 1.0),
            "excavation_score": excavation_score,
        }

    def detect_sites(
        self,
        blue: np.ndarray,
        green: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir1: np.ndarray,
    ) -> np.ndarray:
        """
        Génère un masque binaire booléen des zones présentant une signature d'activité minière.
        """
        indices = self.compute_indices(blue, green, red, nir, swir1)
        bsi = indices["bsi"]
        ndvi = indices["ndvi"]
        score = indices["excavation_score"]

        # Règles de décision spectrales
        mining_mask = (
            (bsi >= self.bsi_threshold)
            & (ndvi <= self.ndvi_max_threshold)
            & (score >= self.min_excavation_score)
        )
        return mining_mask
