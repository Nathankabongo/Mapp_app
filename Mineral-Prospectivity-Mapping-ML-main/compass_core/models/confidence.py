"""Niveaux de confiance."""

from __future__ import annotations

from compass_core.constants import CONFIDENCE_STARS


def stars(level: int) -> str:
    return CONFIDENCE_STARS.get(max(1, min(5, level)), CONFIDENCE_STARS[1])


def infer_confidence(*, official: bool, verifiable: bool, in_model_extent: bool) -> int:
    if official and verifiable:
        return 5
    if verifiable:
        return 4
    if in_model_extent:
        return 3
    return 2
