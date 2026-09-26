#!/usr/bin/env python3
"""Interface CLI CriticalMineralsCompass — mode offline-first."""

from __future__ import annotations

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="critical-compass",
        description="CriticalMineralsCompass — cartographie de prospectivité minérale (RDC)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Exécuter une démo sans dataset (données synthétiques en mémoire)",
    )
    demo_parser.add_argument(
        "--model",
        default="woe",
        choices=["rf", "svm", "ann", "cnn", "woe"],
        help="Modèle à tester (woe par défaut, sans dépendance lourde)",
    )
    demo_parser.add_argument("--output-dir", default="outputs/demo")
    demo_parser.add_argument("--seed", type=int, default=42)

    validate_parser = subparsers.add_parser("validate-config", help="Valider un fichier JSON")
    validate_parser.add_argument("--config", required=True)
    validate_parser.add_argument(
        "--check-files",
        action="store_true",
        help="Vérifier aussi l'existence des fichiers SIG",
    )

    subparsers.add_parser("list-models", help="Lister les modèles disponibles")

    run_parser = subparsers.add_parser("run", help="Lancer un pipeline MPM (fichiers SIG)")
    run_parser.add_argument("--config", required=True)

    split_parser = subparsers.add_parser("split-samples", help="Diviser les échantillons train/test")
    split_parser.add_argument("--samples", required=True)
    split_parser.add_argument("--train-out", required=True)
    split_parser.add_argument("--test-out", required=True)
    split_parser.add_argument("--fraction", type=float, default=0.8)

    sample_parser = subparsers.add_parser(
        "generate-sample-data",
        help="Générer le jeu SIG d'exemple Kolwezi (GeoTIFF + GeoPackage)",
    )
    sample_parser.add_argument("--output-dir", default="data/rdc/kolwezi")
    sample_parser.add_argument("--rows", type=int, default=64)
    sample_parser.add_argument("--cols", type=int, default=64)
    sample_parser.add_argument("--bands", type=int, default=8)
    sample_parser.add_argument("--deposits", type=int, default=60)
    sample_parser.add_argument("--seed", type=int, default=42)

    atlas_parser = subparsers.add_parser(
        "generate-atlas",
        help="Générer l'atlas multi-minéraux RDC (couches GeoPackage)",
    )
    atlas_parser.add_argument("--output-dir", default="data/rdc/atlas")
    atlas_parser.add_argument("--points", type=int, default=25)
    atlas_parser.add_argument("--seed", type=int, default=42)

    import_parser = subparsers.add_parser(
        "import-atlas",
        help="Importer une couche GeoPackage CAMI dans l'atlas",
    )
    import_parser.add_argument("--source", required=True, help="Fichier .gpkg source")
    import_parser.add_argument(
        "--commodity",
        required=True,
        choices=["cu_co", "li", "au", "coltan", "diamond"],
    )
    import_parser.add_argument("--output-dir", default="data/rdc/atlas")

    return parser


def _demo_config(model: str, output_dir: str, seed: int):
    from compass_core.config.demo import build_demo_config

    return build_demo_config(model=model, output_dir=output_dir, seed=seed)


def main(argv: list[str] | None = None) -> int:
    from pathlib import Path

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo":
        from compass_core.pipeline.runner import run_pipeline_synthetic

        config = _demo_config(args.model, args.output_dir, args.seed)
        result = run_pipeline_synthetic(config)
        print(f"Démo terminée — modèle={args.model}")
        print(f"  AUC   = {result.evaluation.auc:.4f}")
        print(f"  Kappa = {result.evaluation.kappa:.4f}")
        print(f"  Provenance : {result.provenance_path}")
        for path in result.output_files:
            print(f"  → {path}")
        return 0

    if args.command == "validate-config":
        from compass_core.config.validate import validate_config

        report = validate_config(args.config, check_files=args.check_files)
        for error in report.errors:
            print(f"ERREUR : {error}")
        for warning in report.warnings:
            print(f"AVERTISSEMENT : {warning}")
        if report.valid:
            assert report.config is not None
            print(f"Configuration valide : {args.config}")
            print(f"  Projet  : {report.config.project_name}")
            print(f"  Région  : {report.config.region.name} ({report.config.region.commodity})")
            print(f"  Modèle  : {report.config.model.name}")
        return 0 if report.valid else 1

    if args.command == "list-models":
        from compass_core.config.schema import SUPPORTED_MODELS

        descriptions = {
            "rf": "Random Forest — robuste, peu de tuning",
            "svm": "Support Vector Machine — noyau RBF",
            "ann": "Réseau dense Keras (nécessite TensorFlow)",
            "cnn": "Conv1D Keras (nécessite TensorFlow)",
            "woe": "Weights of Evidence — MPM classique, léger",
        }
        print("Modèles disponibles :\n")
        for name in SUPPORTED_MODELS:
            print(f"  {name:4}  {descriptions[name]}")
        return 0

    if args.command == "run":
        from compass_core.config.schema import load_config
        from compass_core.pipeline.runner import run_pipeline

        config = load_config(args.config)
        result = run_pipeline(config)
        print(f"Exécution terminée — AUC={result.evaluation.auc:.4f}, Kappa={result.evaluation.kappa:.4f}")
        print(f"Provenance : {result.provenance_path}")
        for path in result.output_files:
            print(f"  → {path}")
        return 0

    if args.command == "split-samples":
        from compass_core.data.vector import split_samples

        split_samples(
            args.samples,
            args.train_out,
            args.test_out,
            train_fraction=args.fraction,
        )
        print(f"Échantillons divisés : {args.train_out}, {args.test_out}")
        return 0

    if args.command == "generate-sample-data":
        from compass_core.data.sample_generator import generate_kolwezi_sample_dataset

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
        print(f"  Gisements    : {report.deposits_path}")
        print(f"  Entraînement : {report.training_path}")
        print(f"  Test         : {report.testing_path}")
        return 0

    if args.command == "generate-atlas":
        from compass_core.analysis.mineral_layers import generate_atlas_layers

        created = generate_atlas_layers(
            args.output_dir,
            points_per_layer=args.points,
            seed=args.seed,
        )
        print("Atlas multi-minéraux généré :")
        for code, path in created.items():
            print(f"  {code:8} → {path}")
        return 0

    if args.command == "import-atlas":
        from compass_core.analysis.atlas_import import import_cami_layer

        report = import_cami_layer(args.source, args.commodity, output_dir=Path(args.output_dir))
        if report.success:
            print(f"Import OK — {report.feature_count} entités → {report.output_path}")
            for canonical, source in report.field_mapping.items():
                print(f"  {canonical} ← {source}")
            return 0
        for err in report.errors:
            print(f"ERREUR : {err}")
        return 1

    return 1


def entry_point() -> None:
    sys.exit(main())


if __name__ == "__main__":
    entry_point()
