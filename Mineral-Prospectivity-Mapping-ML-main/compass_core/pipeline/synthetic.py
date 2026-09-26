"""Jeu de données synthétique pour tests sans fichiers SIG."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SyntheticDataset:
    """Raster et échantillons générés en mémoire."""

    cube: np.ndarray
    flat: np.ndarray
    train_features: np.ndarray
    train_labels: np.ndarray
    test_features: np.ndarray
    test_labels: np.ndarray
    rows: int
    cols: int
    nbands: int

    @property
    def shape_2d(self) -> tuple[int, int]:
        return self.rows, self.cols


def generate_synthetic_dataset(
    *,
    rows: int = 48,
    cols: int = 48,
    nbands: int = 8,
    n_train: int = 80,
    n_test: int = 30,
    seed: int = 42,
) -> SyntheticDataset:
    """
    Génère un raster multi-bandes et des échantillons étiquetés en mémoire.

    Permet de valider le pipeline complet sans GeoTIFF ni shapefile.
    """
    rng = np.random.default_rng(seed)
    cube = rng.normal(size=(rows, cols, nbands)).astype(np.float32)
    cube[:, :, 0] = np.abs(cube[:, :, 0]) + 0.1

    flat = cube.reshape(rows * cols, nbands)

    def sample_points(n: int) -> tuple[np.ndarray, np.ndarray]:
        indices = rng.choice(rows * cols, size=n, replace=False)
        features = flat[indices]
        signal = features[:, 0] + 0.5 * features[:, 1]
        labels = (signal + rng.normal(scale=0.3, size=n) > signal.mean()).astype(float)
        return features, labels

    train_x, train_y = sample_points(n_train)
    test_x, test_y = sample_points(n_test)

    return SyntheticDataset(
        cube=cube,
        flat=flat,
        train_features=train_x,
        train_labels=train_y,
        test_features=test_x,
        test_labels=test_y,
        rows=rows,
        cols=cols,
        nbands=nbands,
    )
