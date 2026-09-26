"""Jetons du design system CriticalMineralsCompass RDC — Style Command Center / Palantir."""

from __future__ import annotations

# Identité Command Center Minier — High-Tech, Cyber-Cartographie, Glassmorphism
COLORS = {
    "bg": "#060A10",               # Noir obsidienne profond
    "chrome": "#0B101A",           # Dark navy de structure
    "elevated": "rgba(13, 22, 36, 0.75)",  # Glassmorphic card surface
    "panel": "rgba(16, 26, 42, 0.85)",     # Panneaux rétractables translucides
    "border": "rgba(255, 255, 255, 0.08)", # Bordure fine luminescente
    "border_strong": "rgba(0, 242, 254, 0.4)", # Bordure cyan réactive
    "text": "#F8FAFC",             # Blanc pur éclatant
    "text_secondary": "#94A3B8",   # Gris ardoise clair
    "text_muted": "#64748B",       # Gris discret
    "accent": "#00F2FE",           # Cyan néon cybernétique
    "accent_glow": "rgba(0, 242, 254, 0.25)",
    "accent_dim": "rgba(0, 242, 254, 0.12)",
    "brand": "#E5A93C",            # Or minéral ambré (Cu/Co/Li/Au)
    "brand_glow": "rgba(229, 169, 60, 0.3)",
    "ok": "#10B981",               # Vert émeraude opérationnel
    "warn": "#F59E0B",             # Ambre alerte
    "danger": "#EF4444",           # Rouge critique
    "info": "#38BDF8",             # Bleu ciel radar
    "demo": "rgba(229, 169, 60, 0.15)",
}

BADGE_STYLES = {
    "official": ("CERTIFIÉ ÉTAT (CAMI/SGN-C)", COLORS["ok"]),
    "open": ("OPEN GEODATA", COLORS["info"]),
    "historical": ("ARCHIVES BNDG", COLORS["info"]),
    "estimated": ("ESTIMATION STATISTIQUE", COLORS["warn"]),
    "modeled": ("MODÈLE GÉOLOGIQUE 3D", "#818CF8"),
    "experimental": ("ANALYTIQUE EXPÉRIMENTAL", COLORS["warn"]),
    "computed": ("GÉOPROCESSING H3", COLORS["accent"]),
    "demo": ("SIMULATION", COLORS["brand"]),
    "unavailable": ("NON COUVERT", COLORS["text_muted"]),
    "imported": ("IMPORT LABORATOIRE", COLORS["info"]),
    "observation": ("TÉLÉDÉTECTION SATELLITE", COLORS["info"]),
    "anomaly": ("SIGNATURE ANOMALIQUE", COLORS["warn"]),
    "prediction": ("GEOAI PRÉDICTIF", "#818CF8"),
    "field": ("CONTRÔLE BIGEMIP/SENTECH", COLORS["warn"]),
    "confirmed": ("GISEMENT VÉRIFIÉ", COLORS["ok"]),
    "measured": ("ASSAYS CERTIFIÉS", COLORS["ok"]),
    "interpolated": ("INTERPOLATION KRIGING", COLORS["warn"]),
    "hypothesis": ("HYPOTHÈSE PROSPECTIVITÉ", COLORS["brand"]),
}

PLATFORM_NAME = "CriticalMineralsCompass"
PLATFORM_TAGLINE = "Exploration Decision Intelligence Layer — RDC"
PLATFORM_REGION = "République Démocratique du Congo"
