"""Pipeline d'exécution."""

from compass_core.pipeline.core import PipelineResult, run_pipeline_core

__all__ = [
    "PipelineResult",
    "run_pipeline_core",
    "run_pipeline",
    "run_pipeline_synthetic",
    "generate_synthetic_dataset",
]


def __getattr__(name: str):
    if name == "run_pipeline":
        from compass_core.pipeline.runner import run_pipeline

        return run_pipeline
    if name == "run_pipeline_synthetic":
        from compass_core.pipeline.runner import run_pipeline_synthetic

        return run_pipeline_synthetic
    if name == "generate_synthetic_dataset":
        from compass_core.pipeline.synthetic import generate_synthetic_dataset

        return generate_synthetic_dataset
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
