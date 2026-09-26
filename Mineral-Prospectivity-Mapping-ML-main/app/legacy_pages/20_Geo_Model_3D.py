"""20 — Geo Model 3D (V1 : forages)."""

from __future__ import annotations

import streamlit as st

from app.components.empty_state import render_warning_state
from app.components.kpi_card import render_kpi_row
from app.components.section_header import render_section
from app.shell import bootstrap, close_page, masthead
from compass_core.drillholes.store import load_demo_drillholes
from compass_core.geology.geological_model import geology_model_status
from compass_core.modelling.kriging import kriging_status
from compass_core.modelling.model3d import LITHO_COLORS, build_scene
from compass_core.modelling.rbf import rbf_status

filters = bootstrap("Geo Model 3D", active_page="Geo Model 3D")
masthead(
    "3D Geological Model",
    "Visualisation progressive du sous-sol — V1 forages ; surfaces / volumes ensuite.",
    sources="modelling · drillholes · RBF/IDW prêts",
)
render_warning_state(
    "Pas de volume de minéralisation inventé. "
    "Mesure / interpolation / prédiction IA restent séparées visuellement.",
    title="Modèle 3D",
)

holes = load_demo_drillholes()
scene = build_scene(holes)
geo = geology_model_status()

render_kpi_row(
    [
        {"label": "Version", "value": "V1", "footnote": scene["version"], "data_class": "computed"},
        {"label": "Forages 3D", "value": str(len(scene["traces"])), "data_class": "demo" if holes else "unavailable"},
        {"label": "RBF", "value": rbf_status()["status"][:12], "data_class": "modeled"},
        {"label": "Krigeage", "value": kriging_status()["status"][:12], "data_class": "unavailable"},
    ]
)

render_section("Couches 3D")
layers_av = scene["layers_available"]
cols = st.columns(4)
for i, (name, ok) in enumerate(layers_av.items()):
    with cols[i % 4]:
        st.checkbox(name, value=ok and name == "drillholes", disabled=not ok, key=f"g3d_{name}")

if not scene["traces"]:
    st.warning(scene["message"])
    st.caption("Roadmap : " + " → ".join(scene["roadmap"]))
    close_page()
    st.stop()

render_section("Vue 3D interactive")
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError as exc:
    HAS_PLOTLY = False
    st.error(f"Plotly indisponible dans l'environnement Python : {exc}")

if HAS_PLOTLY:
    try:
        fig = go.Figure()
        for tr in scene["traces"]:
            fig.add_trace(
                go.Scatter3d(
                    x=tr["x"],
                    y=tr["y"],
                    z=tr["z"],
                    mode="lines+markers",
                    name=tr["hole_id"],
                    line=dict(width=6, color="#2A9D8F"),
                    marker=dict(size=3),
                    hovertemplate=f"{tr['hole_id']}<br>z=%{{z:.0f}} m<extra></extra>",
                )
            )
            # Collar
            fig.add_trace(
                go.Scatter3d(
                    x=[tr["x"][0]],
                    y=[tr["y"][0]],
                    z=[tr["z"][0]],
                    mode="markers+text",
                    text=[tr["hole_id"]],
                    textposition="top center",
                    marker=dict(size=8, color="#C4A35A"),
                    showlegend=False,
                )
            )
            # Color intervals along hole if lithology present
            for iv in tr.get("intervals") or []:
                lith = (iv.get("lithology") or "default").lower()
                color = LITHO_COLORS.get(lith, LITHO_COLORS["default"])
                # approximate segment by depth fraction
                depth = max(tr["z"][0] - tr["z"][-1], 1.0)
                z0 = tr["z"][0] - float(iv["from_m"])
                z1 = tr["z"][0] - float(iv["to_m"])
                fig.add_trace(
                    go.Scatter3d(
                        x=[tr["x"][0], tr["x"][0]],
                        y=[tr["y"][0], tr["y"][0]],
                        z=[z0, z1],
                        mode="lines",
                        line=dict(width=10, color=color),
                        name=f"{tr['hole_id']} {lith}"[:28],
                        showlegend=False,
                        hovertext=f"{lith} {iv['from_m']}-{iv['to_m']} m",
                    )
                )

        fig.update_layout(
            scene=dict(
                xaxis_title="E (m local)",
                yaxis_title="N (m local)",
                zaxis_title="Z (m)",
                aspectmode="data",
                bgcolor="#0B1220",
            ),
            paper_bgcolor="#0B1220",
            font=dict(color="#E8EEF7"),
            margin=dict(l=0, r=0, t=30, b=0),
            height=560,
            legend=dict(orientation="h"),
            title="Forages DEMO — rotation / zoom souris",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.error(f"Erreur lors du rendu du graphique 3D : {exc}")

render_section("Statut modèle géologique")
st.write(geo["message"])
st.json({k: v for k, v in geo.items() if k != "message"})
st.caption("Roadmap : " + " → ".join(scene["roadmap"]))
_ = filters
close_page()
