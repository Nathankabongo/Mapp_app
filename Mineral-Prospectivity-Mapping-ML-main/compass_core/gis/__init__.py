"""Package GIS."""

from compass_core.gis.crs import crs_strategy_doc, resolve_metric_crs
from compass_core.gis.layers import inventory_layers

__all__ = ["crs_strategy_doc", "resolve_metric_crs", "inventory_layers"]
