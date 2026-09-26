"""Chargement et préparation des données raster/vecteur."""

from compass_core.data.fitting import extract_labeled_samples, LabeledSamples

__all__ = [
    "extract_labeled_samples",
    "LabeledSamples",
    "load_raster",
    "write_raster",
    "rasterize_samples",
    "split_samples",
]


def __getattr__(name: str):
    if name in ("load_raster", "write_raster"):
        from compass_core.data import raster as raster_module

        return getattr(raster_module, name)
    if name in ("rasterize_samples", "split_samples"):
        from compass_core.data import vector as vector_module

        return getattr(vector_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
