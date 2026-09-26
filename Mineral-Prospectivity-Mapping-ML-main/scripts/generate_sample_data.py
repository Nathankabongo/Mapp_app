#!/usr/bin/env python3
"""Génère le jeu de données SIG d'exemple Kolwezi."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compass_core.data.sample_generator import generate_kolwezi_sample_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Génère un jeu SIG Kolwezi (GeoTIFF + GeoPackage) pour tests et démo.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/rdc/kolwezi",
        help="Répertoire de sortie (défaut: data/rdc/kolwezi)",
    )
    parser.add_argument("--rows", type=int, default=64)
    parser.add_argument("--cols", type=int, default=64)
    parser.add_argument("--bands", type=int, default=8)
    parser.add_argument("--deposits", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    report = generate_kolwezi_sample_dataset(
        args.output_dir,
        rows=args.rows,
        cols=args.cols,
        nbands=args.bands,
        n_deposits=args.deposits,
        seed=args.seed,
    )

    print("Jeu de données Kolwezi généré :")
    print(f"  Répertoire   : {report.output_dir}")
    print(f"  Raster       : {report.raster_path}")
    print(f"  Gisements    : {report.deposits_path} ({report.n_positive}+ / {report.n_negative}-)")
    print(f"  Entraînement : {report.training_path}")
    print(f"  Test         : {report.testing_path}")
    print(f"  Métadonnées  : {report.metadata_path}")
    print(f"  Taille       : {report.rows}×{report.cols} px, {report.nbands} bandes, {report.crs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
