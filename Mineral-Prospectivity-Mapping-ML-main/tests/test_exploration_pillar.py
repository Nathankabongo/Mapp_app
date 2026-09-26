import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Ajouter d:\Mapping au sys.path
workspace_root = Path("d:/Mapping")
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from src.modules.exploration.geoscience_utils import (
    analytical_signal,
    centered_log_ratio,
    compute_fault_density,
    compute_fault_proximity,
    first_vertical_derivative,
    multivariate_anomaly_score,
)
from src.modules.exploration.site_detection import MiningSiteDetector, filter_and_polygonize_sites
from src.modules.exploration.geological_modeling import GemPyGeologicalModel


class TestExplorationPillar(unittest.TestCase):
    def test_geoscience_magnetics(self):
        grid = np.ones((50, 50)) * 34000.0
        # Ajouter une anomalie au centre
        grid[20:30, 20:30] += 500.0

        vd1 = first_vertical_derivative(grid, cell_size_m=50.0)
        self.assertEqual(vd1.shape, (50, 50))

        as_grid = analytical_signal(grid, cell_size_m=50.0)
        self.assertEqual(as_grid.shape, (50, 50))
        self.assertTrue(np.max(as_grid) > 0)

    def test_geoscience_geochem_clr(self):
        df = pd.DataFrame({
            "Cu": [100.0, 5000.0, 50.0],
            "Co": [10.0, 800.0, 5.0],
            "Fe": [30000.0, 20000.0, 15000.0],
        })
        clr_df = centered_log_ratio(df, ["Cu", "Co", "Fe"])
        self.assertEqual(len(clr_df), 3)
        self.assertIn("Cu_clr", clr_df.columns)
        # La somme des composantes CLR par ligne est approximativement 0
        row_sums = clr_df.sum(axis=1)
        for s in row_sums:
            self.assertAlmostEqual(s, 0.0, places=4)

        scores = multivariate_anomaly_score(df, ["Cu", "Co"])
        self.assertEqual(len(scores), 3)
        # L'échantillon 1 (5000 Cu, 800 Co) doit avoir le score le plus élevé
        self.assertGreater(scores[1], scores[0])

    def test_geoscience_lineaments(self):
        fault_mask = np.zeros((40, 40), dtype=bool)
        fault_mask[20, :] = True

        density = compute_fault_density(fault_mask, sigma=2.0)
        self.assertEqual(density.shape, (40, 40))
        self.assertAlmostEqual(np.max(density), 1.0)

        proximity = compute_fault_proximity(fault_mask, pixel_size_m=50.0)
        self.assertEqual(proximity.shape, (40, 40))
        self.assertAlmostEqual(proximity[20, 20], 1.0)  # Sur la faille = 1.0

    def test_site_detection(self):
        np.random.seed(42)
        blue = np.random.uniform(0.05, 0.15, (60, 60))
        green = np.random.uniform(0.05, 0.15, (60, 60))
        red = np.random.uniform(0.1, 0.2, (60, 60))
        nir = np.random.uniform(0.3, 0.6, (60, 60))
        swir1 = np.random.uniform(0.1, 0.3, (60, 60))

        # Créer une fausse zone minière (forte réflectance sol nu / déforestation)
        red[25:35, 25:35] = 0.45
        swir1[25:35, 25:35] = 0.55
        nir[25:35, 25:35] = 0.15  # Végétation détruite

        detector = MiningSiteDetector(bsi_threshold=0.10, ndvi_max_threshold=0.20)
        mask = detector.detect_sites(blue, green, red, nir, swir1)
        self.assertTrue(np.any(mask))

        features = filter_and_polygonize_sites(mask, min_pixels=4)
        self.assertGreater(len(features), 0)
        self.assertIn("properties", features[0])
        self.assertIn("area_hectares", features[0]["properties"])

    def test_geological_modeling(self):
        model = GemPyGeologicalModel(
            project_name="Test_Model",
            extent=(0, 500, 0, 500, -200, 0),
        )
        block_model = model.compute_model(resolution=(10, 10, 8))
        self.assertEqual(block_model["project_name"], "Test_Model")
        self.assertEqual(block_model["lithology_ids"].shape, (10, 10, 8))

        summary = model.export_summary()
        self.assertIn("total_blocks", summary)
        self.assertEqual(summary["total_blocks"], 800)


if __name__ == "__main__":
    unittest.main()
