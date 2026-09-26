"""CSS global et coquille de page — Design System 'Command Center / Palantir Foundry'."""

from __future__ import annotations

import streamlit as st
from app.components.theme import COLORS, PLATFORM_NAME


def inject_design_system_css() -> None:
    c = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

        /* Base & Typographie */
        html, body, [class*="css"] {{
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: {c["text"]};
            letter-spacing: -0.01em;
        }}

        .stApp {{
            background: radial-gradient(circle at 50% 0%, #0c1524 0%, {c["bg"]} 75%);
            background-attachment: fixed;
        }}

        .block-container {{
            padding-top: 1.2rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1720px;
        }}

        /* Header Streamlit */
        header[data-testid="stHeader"] {{
            background: rgba(6, 10, 16, 0.85) !important;
            backdrop-filter: blur(16px);
            border-bottom: 1px solid {c["border"]};
        }}
        [data-testid="stToolbar"] {{ visibility: hidden; height: 0; }}

        /* —— Navigation Latérale Streamlit (st.navigation) —— */
        [data-testid="stSidebarNav"] {{
            display: block !important;
            visibility: visible !important;
            padding: 0.6rem 0.5rem 0.85rem !important;
            border-bottom: 1px solid {c["border"]};
            margin-bottom: 0.75rem !important;
        }}
        [data-testid="stSidebarNav"] ul {{
            padding: 0 !important;
            list-style: none !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 0.35rem !important;
        }}
        [data-testid="stSidebarNav"] li {{
            margin: 0 !important;
        }}
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"] {{
            color: {c["text_secondary"]} !important;
            background: rgba(255, 255, 255, 0.02) !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.86rem !important;
            padding: 0.55rem 0.85rem !important;
            text-decoration: none !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            border: 1px solid transparent !important;
            display: flex !important;
            align-items: center !important;
        }}
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"]:hover {{
            background: rgba(0, 242, 254, 0.08) !important;
            color: #FFFFFF !important;
            border-color: rgba(0, 242, 254, 0.3) !important;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.15) !important;
            transform: translateX(3px);
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: linear-gradient(90deg, rgba(0, 242, 254, 0.16) 0%, rgba(0, 242, 254, 0.04) 100%) !important;
            color: {c["accent"]} !important;
            font-weight: 600 !important;
            border-left: 3px solid {c["accent"]} !important;
            border-color: rgba(0, 242, 254, 0.35) !important;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.15) !important;
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {{
            background: {c["chrome"]} !important;
            border-right: 1px solid {c["border"]};
            box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
            min-width: 19rem !important;
            width: 19rem !important;
        }}
        div[data-testid="stSidebar"] > div:first-child {{
            padding-top: 0.8rem;
        }}

        /* Marque Sidebar Command Center */
        .cmc-side-brand {{
            position: relative;
            padding: 1rem 1rem 1.25rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid {c["border"]};
            background: linear-gradient(180deg, rgba(0, 242, 254, 0.04) 0%, transparent 100%);
            border-radius: 8px;
        }}
        .cmc-brand-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        .cmc-logo-icon {{
            font-size: 1.6rem;
            color: {c["accent"]};
            text-shadow: 0 0 12px {c["accent"]};
        }}
        .cmc-logo-text {{
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            color: {c["text_secondary"]};
            line-height: 1.2;
        }}
        .cmc-logo-text strong {{
            font-size: 1.05rem;
            letter-spacing: 0.05em;
            color: #FFFFFF;
            font-weight: 800;
        }}
        .cmc-brand-sub {{
            display: flex;
            gap: 0.4rem;
            margin-top: 0.65rem;
        }}
        .badge-tech {{
            background: rgba(0, 242, 254, 0.12);
            color: {c["accent"]};
            border: 1px solid rgba(0, 242, 254, 0.3);
            font-size: 0.6rem;
            font-weight: 700;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            letter-spacing: 0.08em;
        }}
        .badge-geo {{
            background: rgba(229, 169, 60, 0.12);
            color: {c["brand"]};
            border: 1px solid rgba(229, 169, 60, 0.3);
            font-size: 0.6rem;
            font-weight: 700;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            letter-spacing: 0.08em;
        }}

        .cmc-nav-cat {{
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.15em;
            color: {c["text_muted"]};
            text-transform: uppercase;
            padding: 0.5rem 0.2rem 0.3rem;
            margin-top: 0.5rem;
        }}

        /* Health Status Card */
        .cmc-side-health {{
            margin-top: 1.5rem;
            padding: 0.85rem;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid {c["border"]};
            border-radius: 8px;
        }}
        .health-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.6rem;
        }}
        .health-title {{
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            color: {c["text_secondary"]};
        }}
        .health-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            padding: 0.2rem 0;
            color: {c["text_muted"]};
        }}
        .health-val-ok {{
            color: {c["ok"]};
            font-weight: 600;
            font-family: "JetBrains Mono", monospace;
        }}
        .health-val {{
            color: {c["text_secondary"]};
            font-weight: 500;
            font-family: "JetBrains Mono", monospace;
        }}

        /* Animated Pulsing Dot */
        .pulse-dot {{
            width: 8px;
            height: 8px;
            background-color: {c["ok"]};
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px {c["ok"]};
            animation: pulse-green 2s infinite;
        }}
        @keyframes pulse-green {{
            0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}

        /* —— Header de Page Command Center —— */
        .cmc-page-header {{
            background: linear-gradient(180deg, rgba(13, 22, 36, 0.8) 0%, rgba(13, 22, 36, 0.3) 100%);
            backdrop-filter: blur(12px);
            border: 1px solid {c["border"]};
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }}
        .cmc-page-header::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, {c["accent"]} 50%, transparent 100%);
        }}
        .cmc-header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            font-size: 0.7rem;
            font-family: "JetBrains Mono", monospace;
        }}
        .cmc-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            color: {c["ok"]};
            font-weight: 600;
        }}
        .pulse-radar {{
            width: 6px;
            height: 6px;
            background: {c["ok"]};
            border-radius: 50%;
            box-shadow: 0 0 6px {c["ok"]};
        }}
        .cmc-coords-readout {{
            color: {c["accent"]};
            letter-spacing: 0.05em;
        }}
        .cmc-page-kicker {{
            font-size: 0.68rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: {c["accent"]};
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .cmc-page-title {{
            font-size: 1.65rem;
            font-weight: 800;
            color: #FFFFFF !important;
            margin: 0;
            line-height: 1.2;
            letter-spacing: -0.02em;
        }}
        .cmc-page-subtitle {{
            margin: 0.4rem 0 0;
            color: {c["text_secondary"]} !important;
            font-size: 0.92rem;
            line-height: 1.5;
            max-width: 840px;
        }}
        .cmc-page-meta {{
            margin-top: 0.85rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1.25rem;
            font-size: 0.74rem;
            color: {c["text_muted"]};
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 0.75rem;
        }}
        .meta-icon {{
            margin-right: 0.25rem;
        }}

        /* —— KPI Cards (Glassmorphism & Neon) —— */
        .cmc-kpi {{
            background: {c["elevated"]} !important;
            backdrop-filter: blur(16px);
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 1rem 1.25rem;
            min-height: 112px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            transition: all 0.25s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }}
        .cmc-kpi:hover {{
            border-color: rgba(0, 242, 254, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 242, 254, 0.15);
        }}
        .cmc-kpi::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, {c["accent"]} 0%, {c["brand"]} 100%);
            opacity: 0.6;
        }}
        .cmc-kpi-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .cmc-kpi-label {{
            font-size: 0.7rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: {c["text_secondary"]};
            font-weight: 600;
        }}
        .cmc-kpi-icon {{
            font-size: 1rem;
            opacity: 0.8;
        }}
        .cmc-kpi-value-row {{
            display: flex;
            align-items: baseline;
            gap: 0.65rem;
            margin: 0.35rem 0;
        }}
        .cmc-kpi-value {{
            font-size: 1.85rem;
            font-weight: 800;
            color: #FFFFFF;
            font-family: "JetBrains Mono", monospace;
            line-height: 1.1;
        }}
        .cmc-kpi-delta {{
            font-size: 0.7rem;
            font-weight: 600;
            color: {c["ok"]};
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.25);
            padding: 0.12rem 0.4rem;
            border-radius: 4px;
            font-family: "JetBrains Mono", monospace;
        }}
        .cmc-kpi-foot {{
            font-size: 0.72rem;
            color: {c["text_muted"]};
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        .foot-text {{
            color: {c["text_secondary"]};
        }}

        /* Badges High-Tech */
        .cmc-badge {{
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            border: 1px solid;
            line-height: 1.2;
            white-space: nowrap;
        }}

        /* Panels & Containers */
        .cmc-panel {{
            background: {c["panel"]};
            backdrop-filter: blur(16px);
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
        }}
        .cmc-panel-title {{
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: {c["accent"]};
            margin-bottom: 0.85rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* Sections */
        .cmc-section {{
            margin: 1.5rem 0 0.85rem;
        }}
        .cmc-section-title {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {c["text_secondary"]};
            margin: 0;
            padding-bottom: 0.45rem;
            border-bottom: 1px solid {c["border"]};
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* Streamlit Widgets Redesign (Inputs, Buttons, Tabs) */
        .stButton > button {{
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid {c["border"]} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        }}
        .stButton > button:hover {{
            border-color: {c["accent"]} !important;
            color: {c["accent"]} !important;
            box-shadow: 0 0 16px rgba(0, 242, 254, 0.25) !important;
            transform: translateY(-1px);
        }}
        button[kind="primary"] {{
            background: linear-gradient(135deg, {c["accent"]} 0%, #00B4D8 100%) !important;
            color: #060A10 !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.4) !important;
        }}

        /* Streamlit Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem !important;
            background-color: rgba(255, 255, 255, 0.02) !important;
            padding: 0.3rem !important;
            border-radius: 8px !important;
            border: 1px solid {c["border"]} !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 6px !important;
            color: {c["text_secondary"]} !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            padding: 0.45rem 1rem !important;
            border: none !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: rgba(0, 242, 254, 0.15) !important;
            color: {c["accent"]} !important;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.2) !important;
        }}

        /* Custom Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: {c["bg"]};
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {c["accent"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def configure_page(page_title: str) -> None:
    try:
        st.set_page_config(
            page_title=f"{page_title} · {PLATFORM_NAME}",
            page_icon="◈",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass
    inject_design_system_css()
    _pin_sidebar_open()


def _pin_sidebar_open() -> None:
    pass
