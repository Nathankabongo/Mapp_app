# Design system — CriticalMineralsCompass RDC

Identité : **Mining Intelligence + GIS + Decision Support**  
Références UX : IPIS (sidebar sombre + carte dominante), dashboards opérationnels sobres.

## Composants (`app/components/`)

| Module | Rôle |
|--------|------|
| `theme.py` | Couleurs, badges, marque |
| `layout.py` | CSS global + `configure_page` |
| `sidebar.py` | Navigation catégorisée + filtres globaux |
| `header.py` | En-tête de page (titre, meta, sources) |
| `section_header.py` | Titres de section |
| `kpi_card.py` | KPI avec badge de classe de donnée |
| `status_badge.py` / `source_badge.py` | Badges OFFICIEL / DEMO / MODÈLE… |
| `detail_panel.py` | Fiche détail universelle |
| `data_table.py` | Tableaux + recherche |
| `map_panel.py` | Carte + bandeau CRS / sources |
| `empty_state.py` / `warning_state.py` | États vides / alertes |
| `footer.py` | Pied de page |

## Structure de page obligatoire

1. `bootstrap(title, active_page=…)`
2. `masthead(title, subtitle, sources=…)`
3. Sections via `render_section`
4. KPI / filtres / contenu (carte ou table)
5. `close_page()` → footer

## Règle données

Un KPI DEMO ne doit jamais être présenté comme statistique officielle.  
Utiliser `data_class` : `official` | `open` | `historical` | `estimated` | `modeled` | `computed` | `demo` | `unavailable`.
