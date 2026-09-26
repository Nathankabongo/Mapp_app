"""Coquille applicative — bootstrap unique du design system."""

from __future__ import annotations

from app.components.footer import render_footer
from app.components.header import render_page_header
from app.components.layout import configure_page
from app.components.sidebar import DEFAULT_FILTERS, render_sidebar


def bootstrap(page_title: str, *, active_page: str | None = None) -> dict:
    """
    Point d'entrée unique pour chaque page.

    Configure page_config, injecte le CSS, rend la sidebar catégorisée
    et retourne les filtres globaux persistants.
    """
    configure_page(page_title)
    return render_sidebar(active_page=active_page or page_title)


def masthead(
    title: str,
    subtitle: str,
    *,
    sources: str | None = None,
    updated: str | None = None,
) -> None:
    """Compatibilité : délègue au header du design system."""
    render_page_header(title, subtitle, sources=sources, updated=updated)


def close_page() -> None:
    """Pied de page standard — à appeler en fin de chaque page."""
    render_footer()


__all__ = ["bootstrap", "masthead", "close_page", "DEFAULT_FILTERS"]
