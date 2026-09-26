"""Carte Folium de la plateforme."""

from app.national_map import build_national_dashboard_map


def build_platform_map(**kwargs):
    return build_national_dashboard_map(**kwargs)
