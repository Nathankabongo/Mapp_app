"""Réexports analyse spatiale existante."""

from compass_core.spatial.buffer import buffer_wgs84_km
from compass_core.spatial.distance import haversine_km, nearest_feature_km
from compass_core.spatial.proximity import proximity_summary

__all__ = ["buffer_wgs84_km", "haversine_km", "nearest_feature_km", "proximity_summary"]
