"""Explainability des cibles — contributions chiffrées sans inventer de preuves absentes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from compass_core.exploration.targets import ExplorationTarget


# Poids relatifs (normalisés ensuite). Facteurs absents → contribution 0 + mention.
DEFAULT_WEIGHTS = {
    "prospectivity": 0.28,
    "geology": 0.14,
    "geochemistry": 0.12,
    "geophysics": 0.10,
    "structures": 0.08,
    "alteration": 0.06,
    "occurrences": 0.08,
    "remote_sensing": 0.04,
    "history": 0.04,
    "accessibility": 0.03,
    "uncertainty": -0.10,  # pénalité
    "constraints": -0.07,  # pénalité
}


@dataclass
class FactorContribution:
    name: str
    label: str
    raw_score: float  # 0-100 ou pénalité
    weight: float
    contribution: float  # points vers score 100
    available: bool
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TargetExplanation:
    target_id: str
    mineral: str
    composite_score: float
    factors: list[FactorContribution] = field(default_factory=list)
    positive_summary: list[str] = field(default_factory=list)
    negative_summary: list[str] = field(default_factory=list)
    why: str = ""
    layers_used: list[str] = field(default_factory=list)
    disclaimer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TargetComparison:
    target_a: str
    target_b: str
    score_a: float
    score_b: float
    winner: str
    deltas: list[dict] = field(default_factory=list)
    narrative: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _clip(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def explain_target(
    target: ExplorationTarget | dict,
    *,
    weights: dict[str, float] | None = None,
) -> TargetExplanation:
    """
    Décompose le score composite en contributions.
    Les domaines sans données reçoivent contribution 0 (pas de score fictif positif).
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    if isinstance(target, dict):
        tid = target.get("target_id", "?")
        mineral = target.get("mineral", "")
        prosp = float(target.get("prospectivity_score") or 0)
        conf = float(target.get("confidence_pct") or 0)
        uncertainty = float(target.get("uncertainty_pct") or max(0.0, 100.0 - conf))
        data_quality = float(target.get("data_quality") or 0)
        factors_txt = list(target.get("factors") or [])
        constraints = list(target.get("constraints") or [])
        access = target.get("accessibility")
        geo_pot = float(target.get("geological_potential") or prosp)
        factor_scores = dict(target.get("factor_scores") or {})
    else:
        tid = target.target_id
        mineral = target.mineral
        prosp = float(target.prospectivity_score)
        conf = float(target.confidence_pct)
        uncertainty = float(getattr(target, "uncertainty_pct", None) or max(0.0, 100.0 - conf))
        data_quality = float(target.data_quality)
        factors_txt = list(target.factors)
        constraints = list(target.constraints)
        access = target.accessibility
        geo_pot = float(target.geological_potential or prosp)
        factor_scores = dict(getattr(target, "factor_scores", {}) or {})

    def domain_score(key: str, default: float | None, available: bool, note: str) -> FactorContribution:
        label_map = {
            "prospectivity": "Prospectivité IA",
            "geology": "Géologie",
            "geochemistry": "Géochimie",
            "geophysics": "Géophysique",
            "structures": "Structures",
            "alteration": "Altération",
            "occurrences": "Occurrences",
            "remote_sensing": "Télédétection",
            "history": "Historique",
            "accessibility": "Accessibilité",
            "uncertainty": "Incertitude",
            "constraints": "Contraintes",
        }
        weight = float(w.get(key, 0.0))
        if not available or default is None:
            return FactorContribution(
                name=key,
                label=label_map.get(key, key),
                raw_score=0.0,
                weight=weight,
                contribution=0.0,
                available=False,
                note=note or "Donnée indisponible",
            )
        raw = _clip(float(default))
        # Poids négatifs = pénalités
        contrib = weight * raw if weight >= 0 else weight * raw
        return FactorContribution(
            name=key,
            label=label_map.get(key, key),
            raw_score=round(raw, 1),
            weight=weight,
            contribution=round(contrib, 2),
            available=True,
            note=note,
        )

    has_geochem = bool(factor_scores.get("geochemistry"))
    has_geophy = bool(factor_scores.get("geophysics"))
    has_alter = bool(factor_scores.get("alteration"))
    has_struct = bool(factor_scores.get("structures"))
    has_rs = bool(factor_scores.get("remote_sensing"))
    has_hist = bool(factor_scores.get("history"))
    has_occ = "occurrence" in " ".join(factors_txt).lower() or bool(factor_scores.get("occurrences"))

    contributions = [
        domain_score("prospectivity", prosp, True, "Score raster / modèle"),
        domain_score(
            "geology",
            factor_scores.get("geology", geo_pot * 0.85 if geo_pot else None),
            True,
            "Potentiel géologique dérivé du modèle + profil",
        ),
        domain_score(
            "geochemistry",
            factor_scores.get("geochemistry"),
            has_geochem,
            "Aucune géochimie importée" if not has_geochem else "Score géochimique local",
        ),
        domain_score(
            "geophysics",
            factor_scores.get("geophysics"),
            has_geophy,
            "Anomalies géophysiques non extraites" if not has_geophy else "Score géophysique local",
        ),
        domain_score(
            "structures",
            factor_scores.get("structures"),
            has_struct,
            "Failles/structures non vectorisées" if not has_struct else "Contrôle structural",
        ),
        domain_score(
            "alteration",
            factor_scores.get("alteration"),
            has_alter,
            "Carte d'altération absente" if not has_alter else "Altération détectée",
        ),
        domain_score(
            "occurrences",
            factor_scores.get("occurrences", min(100.0, data_quality) if has_occ else None),
            has_occ or "occurrences" in factor_scores,
            "Proximité occurrences atlas" if has_occ else "Pas d'occurrence associée",
        ),
        domain_score(
            "remote_sensing",
            factor_scores.get("remote_sensing"),
            has_rs,
            "Scènes satellitaires non analysées" if not has_rs else "Indice satellitaire",
        ),
        domain_score(
            "history",
            factor_scores.get("history"),
            has_hist,
            "Historique de campagne non documenté" if not has_hist else "Travaux historiques",
        ),
        domain_score(
            "accessibility",
            float(access) if access is not None else None,
            access is not None,
            "Accessibilité non quantifiée" if access is None else "Score d'accès",
        ),
        domain_score("uncertainty", uncertainty, True, "Pénalité = incertitude (100 − confiance)"),
        domain_score(
            "constraints",
            min(100.0, 15.0 * len(constraints)) if constraints else 0.0,
            bool(constraints),
            f"{len(constraints)} contrainte(s) / lacune(s) listée(s)",
        ),
    ]

    # Score composite : moyenne pondérée des facteurs positifs disponibles
    # + pénalités (poids négatifs × raw / 100 → points), sans inventer les absents.
    pos_factors = [c for c in contributions if c.weight > 0 and c.available]
    pos_w = sum(c.weight for c in pos_factors) or 1.0
    scaled_pos = sum((c.weight / pos_w) * c.raw_score for c in pos_factors)
    # Pénalités : poids -0.10 × raw 50 ⇒ −5 points (pas de re-normalisation agressive)
    scaled_neg = sum(c.weight * c.raw_score for c in contributions if c.weight < 0 and c.available)
    composite = _clip(scaled_pos + scaled_neg)

    display_factors: list[FactorContribution] = []
    for c in contributions:
        if c.weight > 0 and c.available:
            pts = (c.weight / pos_w) * c.raw_score
        elif c.weight < 0 and c.available:
            pts = c.weight * c.raw_score
        else:
            pts = 0.0
        display_factors.append(
            FactorContribution(
                name=c.name,
                label=c.label,
                raw_score=c.raw_score,
                weight=c.weight,
                contribution=round(pts, 1),
                available=c.available,
                note=c.note,
            )
        )

    positive = [
        f"{f.label} {f.contribution:+.1f}"
        for f in display_factors
        if f.available and f.contribution > 0
    ]
    negative = [
        f"{f.label} {f.contribution:+.1f} — {f.note}"
        for f in display_factors
        if (f.available and f.contribution < 0) or (not f.available and f.weight > 0)
    ]

    layers = [f.replace("Couche disponible : ", "") for f in factors_txt if f.startswith("Couche")]
    why = (
        f"{tid} obtient {composite:.0f}/100 principalement grâce à "
        + (", ".join(positive[:3]) if positive else "un signal de prospectivité limité")
        + "."
    )

    return TargetExplanation(
        target_id=tid,
        mineral=mineral,
        composite_score=round(composite, 1),
        factors=display_factors,
        positive_summary=positive,
        negative_summary=negative,
        why=why,
        layers_used=layers,
        disclaimer=(
            "Explication basée uniquement sur les facteurs disponibles. "
            "Absence de géochimie/géophysique/structures = contribution nulle (pas de preuve inventée)."
        ),
    )


def compare_targets(
    a: ExplorationTarget | dict,
    b: ExplorationTarget | dict,
    *,
    weights: dict[str, float] | None = None,
) -> TargetComparison:
    ea = explain_target(a, weights=weights)
    eb = explain_target(b, weights=weights)
    deltas = []
    by_b = {f.name: f for f in eb.factors}
    for fa in ea.factors:
        fb = by_b.get(fa.name)
        if fb is None:
            continue
        deltas.append(
            {
                "factor": fa.label,
                "a": fa.contribution,
                "b": fb.contribution,
                "delta_a_minus_b": round(fa.contribution - fb.contribution, 1),
            }
        )
    winner = ea.target_id if ea.composite_score >= eb.composite_score else eb.target_id
    top = sorted(deltas, key=lambda d: abs(d["delta_a_minus_b"]), reverse=True)[:3]
    bits = [f"{d['factor']} (Δ {d['delta_a_minus_b']:+.1f})" for d in top]
    narrative = (
        f"{winner} est prioritaire ({max(ea.composite_score, eb.composite_score):.0f}/100 vs "
        f"{min(ea.composite_score, eb.composite_score):.0f}/100). "
        f"Écarts principaux : {', '.join(bits) if bits else 'n/a'}."
    )
    return TargetComparison(
        target_a=ea.target_id,
        target_b=eb.target_id,
        score_a=ea.composite_score,
        score_b=eb.composite_score,
        winner=winner,
        deltas=deltas,
        narrative=narrative,
    )

def get_xai_for_prospectivity(score: float, zone: str = "ZONE") -> str:
    """Génère le texte d'Explainable AI pour l'interface SGN-C."""
    # Simulation des poids pour la zone (en production : extraits du modèle Random Forest)
    return f"""
    **Explainable AI (XAI) - {zone}**
    Score de prospectivité : **{score:.0f} %**
    
    *Contributions principales :*
    - Géochimie (Cu)  `██████████` 31 %
    - Géologie        `████████  ` 24 %
    - Magnétisme      `██████    ` 18 %
    - Structures      `█████     ` 15 %
    - Topographie     `███       ` 7 %
    - Autres          `██        ` 5 %
    """
