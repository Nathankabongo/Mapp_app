"""Plan d'exploration par cible — phases conditionnelles, jamais forage automatique seul."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def plan_for_target(target: dict, *, diagnostic_gaps: list[str] | None = None) -> dict:
    """
    Plan d'exploration progressif.

    Ne recommande un forage qu'en dernière phase, et seulement si
    confiance suffisante + données de support + confirmation terrain.
    """
    tid = target.get("target_id", "?")
    prosp = float(target.get("prospectivity_score") or 0)
    conf = float(target.get("confidence_pct") or 0)
    unc = float(target.get("uncertainty_pct") or max(0.0, 100.0 - conf))
    unc_label = target.get("uncertainty_label") or (
        "faible" if unc < 25 else "modérée" if unc < 45 else "élevée"
    )
    gaps = list(diagnostic_gaps or [])
    constraints = list(target.get("constraints") or [])
    data_quality = float(target.get("data_quality") or 0)

    phases: list[dict] = []

    # Phase 1 — toujours cartographie / revue données
    phases.append(
        {
            "phase": 1,
            "name": "Revue & cartographie géologique",
            "actions": [
                "Compiler géologie / structures disponibles",
                "Vérifier occurrences et travaux historiques",
                "Contrôler contraintes cadastrales / accès",
            ],
            "required": True,
            "gate": "Compléter l'inventaire avant acquisition terrain",
        }
    )

    # Phase 2 — géochimie si manquante
    need_geochem = any("géochim" in g.lower() for g in gaps + constraints) or data_quality < 55
    phases.append(
        {
            "phase": 2,
            "name": "Géochimie détaillée",
            "actions": [
                "Échantillonnage sols / sédiments / roches (selon accès)",
                "Analyses labo multi-éléments du profil minéral",
                "Cartographier anomalies et les croiser à la prospectivité",
            ],
            "required": bool(need_geochem),
            "status": "RECOMMANDÉ" if need_geochem else "OPTIONNEL",
            "gate": "Confirmer ou infirmer l'anomalie géochimique",
        }
    )

    # Phase 3 — géophysique si manquante / démo seulement
    need_geophy = any("géophys" in g.lower() for g in gaps + constraints)
    phases.append(
        {
            "phase": 3,
            "name": "Levés géophysiques",
            "actions": [
                "Magnétisme / gravimétrie / EM selon contexte métallogénique",
                "Interprétation structurale",
            ],
            "required": bool(need_geophy),
            "status": "RECOMMANDÉ" if need_geophy else "SELON BUDGET",
            "gate": "Réduire l'incertitude structurale avant forage",
        }
    )

    # Phase 4 — validation terrain (toujours avant forage)
    phases.append(
        {
            "phase": 4,
            "name": "Validation terrain",
            "actions": [
                "Visite géologue — affleurements, altération, structures",
                "Contrôle GPS des points Smart Sampling prioritaires",
                "Mettre à jour le diagnostic de zone",
            ],
            "required": True,
            "gate": "Décision go / no-go documentée",
        }
    )

    # Phase 5 — forage conditionnel
    drill_ok = (
        prosp >= 70
        and conf >= 55
        and unc_label in {"faible", "modérée"}
        and data_quality >= 45
    )
    if prosp >= 70 and conf < 55:
        drill_decision = "NON RECOMMANDÉ POUR L'INSTANT"
        drill_reason = (
            f"Prospectivité élevée ({prosp:.0f}) mais confiance insuffisante ({conf:.0f} %). "
            "Compléter géochimie / terrain avant tout forage."
        )
    elif prosp >= 70 and unc_label in {"élevée", "très élevée"}:
        drill_decision = "NON RECOMMANDÉ POUR L'INSTANT"
        drill_reason = (
            f"Incertitude {unc_label} — prioriser Smart Sampling et validation terrain."
        )
    elif drill_ok:
        drill_decision = "CONDITIONNEL"
        drill_reason = (
            "Forage envisageable UNIQUEMENT si les phases 1–4 sont confirmatoires "
            "et validées par un géologue."
        )
    else:
        drill_decision = "NON PRIORITAIRE"
        drill_reason = (
            "Score / confiance / qualité des données insuffisants pour justifier un forage."
        )

    phases.append(
        {
            "phase": 5,
            "name": "Forage (si confirmatoire)",
            "actions": [
                "Définir collar / profondeur avec géologue",
                "Programme lithologie + assays",
                "Intégrer résultats → mise à jour modèles",
            ],
            "required": False,
            "status": drill_decision,
            "gate": drill_reason,
        }
    )

    estimated_cost = (
        "élevé"
        if drill_decision == "CONDITIONNEL"
        else ("moyen" if need_geophy or need_geochem else "faible à moyen")
    )

    return {
        tid: {
            "target_id": tid,
            "prospectivity": prosp,
            "confidence_pct": conf,
            "uncertainty_pct": unc,
            "uncertainty_label": unc_label,
            "phases": phases,
            "drill_decision": drill_decision,
            "drill_reason": drill_reason,
            "estimated_relative_cost": estimated_cost,
            "accessibility": (
                target.get("accessibility")
                if target.get("accessibility") is not None
                else UNAVAILABLE
            ),
            "routes": UNAVAILABLE,
            "avoid_zones": UNAVAILABLE,
            "coordinates": {
                "latitude": target.get("latitude"),
                "longitude": target.get("longitude"),
            },
            "area_km2": target.get("area_km2"),
            "next_action": phases[0]["name"]
            if not drill_ok
            else "Enchaîner phases 1–4 puis réévaluer forage",
            "disclaimer": (
                "Plan indicatif d'exploration. "
                "Aucun forage automatique sur seul score ML. "
                "Itinéraires / aires protégées : NON DISPONIBLES sans couches dédiées."
            ),
            "data_class": "prediction",
            # rétrocompat page Campagne
            "action": "Plan d'exploration progressif",
            "steps": [p["name"] for p in phases],
        }
    }


def plan_campaign_targets(
    targets: list[dict],
    *,
    diagnostic_gaps: list[str] | None = None,
    top_n: int = 5,
) -> dict:
    """Agrège les plans des N premières cibles."""
    plans = {}
    for t in targets[:top_n]:
        plans.update(plan_for_target(t, diagnostic_gaps=diagnostic_gaps))
    return {
        "plans": plans,
        "count": len(plans),
        "disclaimer": "Chaque plan reste soumis à validation géologue / HSE / permis.",
    }
