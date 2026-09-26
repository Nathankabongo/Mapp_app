"""Alias source_badge → status_badge (API demandée)."""

from app.components.status_badge import render_source_badge, render_status_badge, status_badge_html

__all__ = ["render_source_badge", "render_status_badge", "status_badge_html"]
