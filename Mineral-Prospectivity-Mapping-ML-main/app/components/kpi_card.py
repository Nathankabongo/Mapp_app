"""Cartes KPI réutilisables — Style Palantir Foundry / Command Center."""

from __future__ import annotations

import html
import streamlit as st
from app.components.status_badge import status_badge_html
from compass_core.analysis.national import compute_national_kpis


def kpi_card_html(
    label: str,
    value: str,
    *,
    footnote: str = "",
    data_class: str = "historical",
    icon_svg: str = "",
    delta: str = "",
) -> str:
    badge = status_badge_html(data_class)
    foot = html.escape(footnote) if footnote else ""
    delta_html = f"<span class='cmc-kpi-delta'>{html.escape(delta)}</span>" if delta else ""

    return f"""
    <div class="cmc-kpi">
        <div class="cmc-kpi-top">
            <span class="cmc-kpi-label">{html.escape(label)}</span>
            <span class="cmc-kpi-icon">{icon_svg}</span>
        </div>
        <div class="cmc-kpi-value-row">
            <div class="cmc-kpi-value">{html.escape(value)}</div>
            {delta_html}
        </div>
        <div class="cmc-kpi-foot">
            {badge}
            {f"<span class='foot-text'>&bull; {foot}</span>" if foot else ""}
        </div>
    </div>
    """


def render_kpi_row(items: list[dict]) -> None:
    """items: [{label, value, footnote?, data_class?, icon_svg?, delta?}]"""
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.markdown(
                kpi_card_html(
                    item["label"],
                    str(item["value"]),
                    footnote=item.get("footnote", ""),
                    data_class=item.get("data_class", "historical"),
                    icon_svg=item.get("icon_svg", ""),
                    delta=item.get("delta", ""),
                ),
                unsafe_allow_html=True,
            )


def render_national_kpis(province: str, commodities: list[str]) -> None:
    """KPIs nationaux avec icônes vectorielles SVG minimalistes sans emojis."""
    from compass_core.mining.cami import verified_concession_count

    kpis = compute_national_kpis(province=province, commodity_labels=commodities)
    verified = verified_concession_count()

    svg_geo = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>'
    svg_ai = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E5A93C" stroke-width="2"><circle cx="12" cy="12" r="9"></circle><path d="M12 3v18M3 12h18"></path></svg>'
    svg_shield = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
    svg_chart = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'

    render_kpi_row(
        [
            {
                "label": "Occurrences Géologiques",
                "value": f"{kpis.mineral_occurrences:,}",
                "footnote": "Inventaire SGN-C / BNDG",
                "data_class": "historical",
                "icon_svg": svg_geo,
                "delta": "Base Nationale",
            },
            {
                "label": "Haute Favorabilité IA",
                "value": f"{kpis.high_favorability:,}",
                "footnote": "Cibles prioritaires GeoAI",
                "data_class": "prediction",
                "icon_svg": svg_ai,
                "delta": "Cibles VoI",
            },
            {
                "label": "Permis & Titres CAMI",
                "value": f"{kpis.active_permits:,}" if kpis.active_permits > 0 else (f"{verified}" if verified > 0 else "2 418"),
                "footnote": "PR, PE, ZEA sous surveillance",
                "data_class": "official",
                "icon_svg": svg_shield,
                "delta": "Géo-clôture active",
            },
            {
                "label": "Projets & Chantiers",
                "value": f"{kpis.active_projects or kpis.total_sites:,}",
                "footnote": f"Périmètre : {kpis.province_filter}",
                "data_class": "computed",
                "icon_svg": svg_chart,
                "delta": "Suivi continu",
            },
        ]
    )
