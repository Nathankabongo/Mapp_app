#!/usr/bin/env python3
"""Export de la spécification OpenAPI au format PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def export_openapi_pdf(output_path: str | Path, *, openapi_schema: dict | None = None) -> Path:
    """
    Génère un PDF récapitulatif de l'API à partir du schéma OpenAPI.

    Nécessite ``reportlab`` (``pip install -e ".[report]"``).
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise ImportError("reportlab requis : pip install -e '.[report]'") from exc

    if openapi_schema is None:
        root = Path(__file__).resolve().parents[1]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from api.main import app

        openapi_schema = app.openapi()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(out), pagesize=A4, title="CriticalMineralsCompass API")
    styles = getSampleStyleSheet()
    story = []

    info = openapi_schema.get("info", {})
    story.append(Paragraph(f"<b>{info.get('title', 'API')}</b>", styles["Title"]))
    story.append(Paragraph(f"Version {info.get('version', 'N/A')}", styles["Normal"]))
    story.append(Paragraph(info.get("description", ""), styles["Normal"]))
    story.append(Spacer(1, 16))

    rows = [["Méthode", "Chemin", "Résumé"]]
    for path, methods in sorted(openapi_schema.get("paths", {}).items()):
        for method, details in methods.items():
            if method.startswith("x-"):
                continue
            summary = details.get("summary") or str(details.get("description", ""))[:80]
            rows.append([method.upper(), path, summary])

    table = Table(rows, colWidths=[60, 180, 240])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 16))

    schema_path = out.with_suffix(".json")
    schema_path.write_text(json.dumps(openapi_schema, indent=2, ensure_ascii=False), encoding="utf-8")
    story.append(Paragraph(f"Schéma OpenAPI JSON : {schema_path.name}", styles["Italic"]))

    doc.build(story)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenAPI → PDF")
    parser.add_argument("--output", default="outputs/docs/api_reference.pdf")
    args = parser.parse_args()
    path = export_openapi_pdf(args.output)
    print(f"PDF généré : {path}")
    print(f"OpenAPI JSON : {path.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
