"""Validation de configuration et vérification des chemins."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from compass_core.config.schema import CompassConfig, load_config


@dataclass
class ValidationReport:
    """Rapport de validation d'une configuration."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    config: CompassConfig | None = None


def validate_config(path: str | Path, *, check_files: bool = False) -> ValidationReport:
    """
    Valide un fichier JSON de configuration.

    ``check_files=True`` vérifie aussi l'existence des chemins SIG (optionnel).
    """
    errors: list[str] = []
    warnings: list[str] = []
    config: CompassConfig | None = None

    try:
        config = load_config(path)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        return ValidationReport(valid=False, errors=errors, warnings=warnings)

    if check_files and config is not None:
        for label, file_path in (
            ("raster", config.data.raster),
            ("training", config.data.training),
            ("testing", config.data.testing),
        ):
            if not file_path.startswith("(") and not Path(file_path).exists():
                warnings.append(f"Fichier {label} introuvable : {file_path}")

        if (
            config.data.samples
            and not config.data.samples.startswith("(")
            and not Path(config.data.samples).exists()
        ):
            warnings.append(f"Fichier samples introuvable : {config.data.samples}")

    return ValidationReport(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        config=config,
    )


def validate_compass_config(config: CompassConfig) -> ValidationReport:
    """Vérifie l'existence des fichiers SIG pour une config déjà parsée."""
    warnings: list[str] = []
    for label, file_path in (
        ("raster", config.data.raster),
        ("training", config.data.training),
        ("testing", config.data.testing),
    ):
        if not file_path.startswith("(") and not Path(file_path).exists():
            warnings.append(f"Fichier {label} introuvable : {file_path}")

    if (
        config.data.samples
        and not config.data.samples.startswith("(")
        and not Path(config.data.samples).exists()
    ):
        warnings.append(f"Fichier samples introuvable : {config.data.samples}")

    return ValidationReport(valid=True, errors=[], warnings=warnings, config=config)
