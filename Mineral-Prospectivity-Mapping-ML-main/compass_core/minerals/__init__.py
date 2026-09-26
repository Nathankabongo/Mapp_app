"""Package profils minéraux multi-substances.

Les helpers zone (recommended_model_for, etc.) s'importent depuis
``compass_core.minerals.zone_knowledge`` pour éviter les imports circulaires.
"""

from compass_core.minerals.profiles import (
    MineralProfile,
    get_profile,
    list_mineral_names,
    list_profiles,
    mineral_supports_raster,
)

__all__ = [
    "MineralProfile",
    "get_profile",
    "list_mineral_names",
    "list_profiles",
    "mineral_supports_raster",
]
