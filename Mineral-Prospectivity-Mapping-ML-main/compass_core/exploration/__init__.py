"""Exploration package — cœur métier CriticalMineralsCompass."""

from compass_core.exploration.campaign import ExplorationCampaign, run_campaign
from compass_core.exploration.diagnostic import ZoneDiagnostic, diagnose_zone
from compass_core.exploration.explainability import (
    TargetComparison,
    TargetExplanation,
    compare_targets,
    explain_target,
)
from compass_core.exploration.history import list_campaigns, save_campaign
from compass_core.exploration.planning import plan_campaign_targets, plan_for_target
from compass_core.exploration.ranking import rank_targets, top_n
from compass_core.exploration.smart_sampling import recommend_samples
from compass_core.exploration.targets import ExplorationTarget, generate_targets
from compass_core.exploration.uncertainty_map import build_uncertainty_map

__all__ = [
    "ExplorationCampaign",
    "ExplorationTarget",
    "ZoneDiagnostic",
    "TargetExplanation",
    "TargetComparison",
    "run_campaign",
    "generate_targets",
    "rank_targets",
    "top_n",
    "diagnose_zone",
    "explain_target",
    "compare_targets",
    "build_uncertainty_map",
    "recommend_samples",
    "plan_for_target",
    "plan_campaign_targets",
    "save_campaign",
    "list_campaigns",
]
