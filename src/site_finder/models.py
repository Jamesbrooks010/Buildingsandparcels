"""Domain models for parcel feasibility screening.

The core models intentionally use the Python standard library so the screening engine can run in
Codex Cloud before project dependencies are installed. The web API adds FastAPI/Pydantic only at the
application boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class MatchStatus(StrEnum):
    """High-level result status for a parcel assessment."""

    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


@dataclass
class BuildingEnvelope:
    """User supplied building type or explicit envelope assumptions."""

    name: str
    storeys: int
    footprint_sqm: float
    building_width_m: float | None = None
    building_depth_m: float | None = None
    building_height_m: float | None = None
    gross_floor_area_sqm: float | None = None
    minimum_site_area_sqm: float | None = None
    maximum_design_site_coverage: float | None = None
    required_frontage_m: float = 0
    required_depth_m: float = 0
    required_zone_codes: list[str] = field(default_factory=list)
    required_zone_categories: list[str] = field(default_factory=list)
    assumptions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.storeys = _positive_int(self.storeys, "storeys")
        self.footprint_sqm = _positive_float(self.footprint_sqm, "footprint_sqm")
        self.building_width_m = _optional_positive_float(
            self.building_width_m, "building_width_m"
        )
        self.building_depth_m = _optional_positive_float(
            self.building_depth_m, "building_depth_m"
        )
        self.building_height_m = _optional_positive_float(
            self.building_height_m, "building_height_m"
        )
        if (
            self.building_width_m is not None
            and self.building_depth_m is not None
            and self.building_width_m * self.building_depth_m < self.footprint_sqm
        ):
            raise ValueError("building_width_m * building_depth_m must cover footprint_sqm.")
        self.gross_floor_area_sqm = _optional_positive_float(
            self.gross_floor_area_sqm, "gross_floor_area_sqm"
        )
        self.minimum_site_area_sqm = _optional_positive_float(
            self.minimum_site_area_sqm, "minimum_site_area_sqm"
        )
        self.maximum_design_site_coverage = _optional_ratio(
            self.maximum_design_site_coverage, "maximum_design_site_coverage"
        )
        self.required_frontage_m = _non_negative_float(
            self.required_frontage_m, "required_frontage_m"
        )
        self.required_depth_m = _non_negative_float(self.required_depth_m, "required_depth_m")
        self.required_zone_codes = [zone.strip().upper() for zone in self.required_zone_codes if zone.strip()]
        self.required_zone_categories = [
            category.strip() for category in self.required_zone_categories if category.strip()
        ]

    @property
    def effective_gfa_sqm(self) -> float:
        return self.gross_floor_area_sqm or self.footprint_sqm * self.storeys

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "BuildingEnvelope":
        return cls(**payload)

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanningControls:
    """Planning controls that can be attached to a parcel."""

    zone_code: str
    zone_name: str | None = None
    max_storeys: int | None = None
    max_building_height_m: float | None = None
    max_site_coverage: float | None = None
    max_floor_area_ratio: float | None = None
    min_site_area_sqm: float | None = None
    min_frontage_m: float | None = None
    max_frontage_m: float | None = None
    min_front_setback_m: float | None = None
    min_rear_setback_m: float | None = None
    min_side_setback_m: float | None = None
    overlays: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        self.zone_code = self.zone_code.strip().upper()
        self.max_storeys = None if self.max_storeys is None else _positive_int(self.max_storeys, "max_storeys")
        self.max_building_height_m = _optional_positive_float(
            self.max_building_height_m, "max_building_height_m"
        )
        self.max_site_coverage = _optional_positive_float(self.max_site_coverage, "max_site_coverage")
        self.max_floor_area_ratio = _optional_positive_float(
            self.max_floor_area_ratio, "max_floor_area_ratio"
        )
        self.min_site_area_sqm = _optional_positive_float(self.min_site_area_sqm, "min_site_area_sqm")
        self.min_frontage_m = _optional_positive_float(self.min_frontage_m, "min_frontage_m")
        self.max_frontage_m = _optional_positive_float(self.max_frontage_m, "max_frontage_m")
        if (
            self.min_frontage_m is not None
            and self.max_frontage_m is not None
            and self.min_frontage_m > self.max_frontage_m
        ):
            raise ValueError("min_frontage_m cannot exceed max_frontage_m.")
        self.min_front_setback_m = _optional_non_negative_float(
            self.min_front_setback_m, "min_front_setback_m"
        )
        self.min_rear_setback_m = _optional_non_negative_float(
            self.min_rear_setback_m, "min_rear_setback_m"
        )
        self.min_side_setback_m = _optional_non_negative_float(
            self.min_side_setback_m, "min_side_setback_m"
        )

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "PlanningControls":
        return cls(**payload)

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Parcel:
    """Parcel attributes required by the first-pass feasibility engine."""

    parcel_id: str
    land_area_sqm: float
    planning: PlanningControls | dict[str, Any]
    address: str | None = None
    suburb: str | None = None
    frontage_m: float | None = None
    depth_m: float | None = None
    geometry_ref: str | None = None
    map_x: float | None = None
    map_y: float | None = None
    map_crs: str | None = None

    def __post_init__(self) -> None:
        self.land_area_sqm = _positive_float(self.land_area_sqm, "land_area_sqm")
        self.frontage_m = _optional_non_negative_float(self.frontage_m, "frontage_m")
        self.depth_m = _optional_non_negative_float(self.depth_m, "depth_m")
        self.map_x = _optional_float(self.map_x, "map_x")
        self.map_y = _optional_float(self.map_y, "map_y")
        if isinstance(self.planning, dict):
            self.planning = PlanningControls.model_validate(self.planning)

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "Parcel":
        return cls(**payload)

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuleOutcome:
    """Outcome of one feasibility rule."""

    rule: str
    status: MatchStatus
    message: str


@dataclass
class ParcelAssessment:
    """Aggregated parcel assessment returned by the API and CLI."""

    parcel: Parcel
    status: MatchStatus
    score: float
    outcomes: list[RuleOutcome]

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return asdict(self)


def _positive_int(value: int, field_name: str) -> int:
    value = int(value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return value


def _positive_float(value: float, field_name: str) -> float:
    value = float(value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return value


def _optional_positive_float(value: float | None, field_name: str) -> float | None:
    return None if value is None else _positive_float(value, field_name)


def _non_negative_float(value: float, field_name: str) -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
    return value


def _optional_non_negative_float(value: float | None, field_name: str) -> float | None:
    return None if value is None else _non_negative_float(value, field_name)


def _optional_ratio(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    value = _positive_float(value, field_name)
    if value > 1:
        raise ValueError(f"{field_name} must not exceed 1.")
    return value


def _optional_float(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc
