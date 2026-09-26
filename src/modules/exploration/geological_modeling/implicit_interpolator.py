"""Interpolateur géologique implicite 3D basé sur les fonctions à base radiale (RBF)."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import RBFInterpolator


class ImplicitPotentialField:
    """
    Modélisateur géologique implicite 3D (méthode du champ de potentiel).
    Permet d'interpoler des couches minéralisées et contacts lithologiques
    à partir de points de forages et de mesures structurales (pendage, azimut).
    """

    def __init__(self, kernel: str = "thin_plate_spline", smoothing: float = 0.01):
        self.kernel = kernel
        self.smoothing = smoothing
        self._interpolator = None
        self.surface_names: list[str] = []
        self.scalar_thresholds: dict[str, float] = {}

    def fit(
        self,
        points: np.ndarray,  # Shape (N, 3): X, Y, Z
        scalar_values: np.ndarray,  # Shape (N,): valeur de potentiel (0.0, 1.0, etc.)
        surface_names: list[str] | None = None,
        thresholds: dict[str, float] | None = None,
    ):
        """Ajuste le champ de potentiel sur les points d'observation géologiques."""
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Les points doivent être un tableau 2D de forme (N, 3).")

        self.surface_names = surface_names or ["Bedrock", "OreBody", "Overburden"]
        self.scalar_thresholds = thresholds or {"OreBody": 1.0, "Bedrock": 0.0}

        self._interpolator = RBFInterpolator(
            points,
            scalar_values,
            kernel=self.kernel,
            smoothing=self.smoothing,
        )

    def evaluate_grid(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        z_range: tuple[float, float],
        resolution: tuple[int, int, int] = (30, 30, 20),
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Évalue le modèle de blocs 3D régulier.
        Retourne (potential_field_3d, lithology_ids_3d).
        """
        if self._interpolator is None:
            raise RuntimeError("Le modèle implicite doit être ajusté via fit() avant évaluation.")

        nx, ny, nz = resolution
        xs = np.linspace(x_range[0], x_range[1], nx)
        ys = np.linspace(y_range[0], y_range[1], ny)
        zs = np.linspace(z_range[0], z_range[1], nz)

        # Génération du maillage 3D
        gx, gy, gz = np.meshgrid(xs, ys, zs, indexing="ij")
        grid_points = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])

        # Prédiction du champ de potentiel
        potential_flat = self._interpolator(grid_points)
        potential_3d = potential_flat.reshape(nx, ny, nz)

        # Classification en unités lithologiques
        litho_3d = np.zeros_like(potential_3d, dtype=int)
        # Seuil par défaut : < 0.5 = Stérile de base (0), 0.5 - 1.5 = Corps minéralisé (1), > 1.5 = Mort-terrain (2)
        litho_3d[potential_3d >= 0.5] = 1
        litho_3d[potential_3d >= 1.5] = 2

        return potential_3d, litho_3d
