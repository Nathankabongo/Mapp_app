"""Modèles de forage — collar / survey / intervals."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Collar:
    hole_id: str
    x: float
    y: float
    z: float
    azimuth: float = 0.0
    dip: float = -90.0  # négatif = vers le bas
    depth_m: float = 0.0
    crs: str = "EPSG:4326"
    data_class: str = "imported"
    source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SurveyStation:
    hole_id: str
    depth_m: float
    azimuth: float
    dip: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Interval:
    hole_id: str
    from_m: float
    to_m: float
    lithology: str = ""
    alteration: str = ""
    mineralization: str = ""
    assay_element: str | None = None
    assay_value: float | None = None
    assay_unit: str | None = None
    assay_data_class: str = "unavailable"  # measured | interpolated | prediction | unavailable
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Drillhole:
    collar: Collar
    surveys: list[SurveyStation] = field(default_factory=list)
    intervals: list[Interval] = field(default_factory=list)

    @property
    def hole_id(self) -> str:
        return self.collar.hole_id

    def to_dict(self) -> dict:
        return {
            "collar": self.collar.to_dict(),
            "surveys": [s.to_dict() for s in self.surveys],
            "intervals": [i.to_dict() for i in self.intervals],
        }
