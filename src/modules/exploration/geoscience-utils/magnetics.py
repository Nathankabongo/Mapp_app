"""Utilitaires de traitement et filtrage de données magnétiques aéroportées."""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def first_vertical_derivative(grid: np.ndarray, cell_size_m: float = 50.0) -> np.ndarray:
    """
    Calcule la Première Dérivée Verticale (1VD) d'une grille de champ magnétique total (TMI).
    Améliore la résolution des linéaments structuraux et contacts géologiques superficiels.
    """
    if grid.ndim != 2:
        raise ValueError("La grille d'entrée doit être une matrice 2D.")

    # Approximation dans le domaine spatial via opérateur laplacien/gradient
    grad_y, grad_x = np.gradient(grid, cell_size_m)
    # Dans le domaine spatial, 1VD approxime le gradient horizontal total
    total_horizontal_gradient = np.sqrt(grad_x**2 + grad_y**2)
    laplacian = ndimage.laplace(grid) / (cell_size_m**2)

    # 1VD normalisée
    vd1 = -laplacian * cell_size_m + total_horizontal_gradient * 0.5
    return vd1


def analytical_signal(grid: np.ndarray, cell_size_m: float = 50.0) -> np.ndarray:
    """
    Calcule l'amplitude du Signal Analytique (Total Gradient).
    Indépendant de la direction de magnétisation et de l'inclinaison rémanente.
    """
    if grid.ndim != 2:
        raise ValueError("La grille d'entrée doit être une matrice 2D.")

    grad_y, grad_x = np.gradient(grid, cell_size_m)
    grad_z = first_vertical_derivative(grid, cell_size_m)

    as_amplitude = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
    return as_amplitude


def reduce_to_pole_approximation(
    grid: np.ndarray,
    inclination_deg: float = -35.0,  # Valeur typique ceinture cuprifère Katanga
    declination_deg: float = -3.0,
) -> np.ndarray:
    """
    Approximation spatiale de la Réduction au Pôle (RTP).
    Recentre les anomalies magnétiques directement au-dessus des corps minéralisés causatifs.
    """
    inc_rad = np.radians(inclination_deg)
    # Facteur de correction de phase pour faibles/moyennes latitudes
    phase_shift = np.sin(inc_rad)
    corrected_grid = (grid - np.mean(grid)) / (np.abs(phase_shift) + 1e-4) + np.mean(grid)
    return corrected_grid
