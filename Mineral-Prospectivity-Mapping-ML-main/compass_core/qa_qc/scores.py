"""Scores QA/QC — distincts du score de prospectivité."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class QCIssue:
    code: str
    severity: str  # info | warning | error
    message: str
    field: str = ""
    record_index: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DataQualityScore:
    completeness: float = 0.0
    accuracy: float = 0.0
    consistency: float = 0.0
    recency: float = 0.0
    spatial_resolution: float = 0.0
    source_reliability: float = 0.0
    scientific_quality: float = 0.0
    processing_quality: float = 0.0

    def global_score(self) -> float:
        vals = [
            self.completeness,
            self.accuracy,
            self.consistency,
            self.recency,
            self.spatial_resolution,
            self.source_reliability,
            self.scientific_quality,
            self.processing_quality,
        ]
        return round(sum(vals) / len(vals), 1)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["global_score"] = self.global_score()
        return d


@dataclass
class QCReport:
    dataset_id: str
    dataset_name: str
    passed: bool
    score: DataQualityScore
    issues: list[QCIssue] = field(default_factory=list)
    n_records: int = 0
    n_checked: int = 0
    spatial: dict = field(default_factory=dict)
    temporal: dict = field(default_factory=dict)
    scientific: dict = field(default_factory=dict)
    geochemical: dict = field(default_factory=dict)
    evidence_level: str = "OBSERVATION"
    data_class: str = "UNAVAILABLE"
    disclaimer: str = (
        "QA/QC contrôle la qualité des données — distinct du score de prospectivité."
    )

    def to_dict(self) -> dict:
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "passed": self.passed,
            "score": self.score.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
            "n_records": self.n_records,
            "n_checked": self.n_checked,
            "spatial": self.spatial,
            "temporal": self.temporal,
            "scientific": self.scientific,
            "geochemical": self.geochemical,
            "evidence_level": self.evidence_level,
            "data_class": self.data_class,
            "disclaimer": self.disclaimer,
        }
