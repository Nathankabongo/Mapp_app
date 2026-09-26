"""Cartes et badges — compatibilité."""

from app.components.empty_state import render_empty_state
from app.components.source_badge import render_source_badge
from app.components.status_badge import render_status_badge


def data_badge(data_class: str, official: str, verifiable: str, confidence: int) -> None:
    render_source_badge(
        source=f"Officiel={official} · Vérifiable={verifiable}",
        data_class=data_class,
        confidence=str(confidence),
    )


def unavailable() -> None:
    render_empty_state(
        "Information non disponible",
        "Information non disponible dans les sources utilisées.",
        status="NON DISPONIBLE",
    )
