from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

NetworkMode = Literal["drive", "walk", "bike", "transit_rail"]
AnalysisProfile = Literal["mobility", "accessibility", "resilience", "urban_morphology", "multimodal"]
AoiMode = Literal["place_name", "bbox", "polygon", "geojson"]


class AreaOfInterest(BaseModel):
    mode: AoiMode
    value: Any

    @model_validator(mode="after")
    def validate_shape(self) -> AreaOfInterest:
        if self.mode == "place_name":
            if not isinstance(self.value, str) or len(self.value.strip()) < 3:
                raise ValueError("place_name AOI must be a non-empty, specific place string")
        elif self.mode == "bbox":
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 4:
                raise ValueError("bbox AOI must be [west, south, east, north]")
        elif self.mode == "polygon":
            if not isinstance(self.value, (dict, list)):
                raise ValueError("polygon AOI must be GeoJSON-like data or coordinate pairs")
        elif self.mode == "geojson" and not isinstance(self.value, dict):
            raise ValueError("geojson AOI must be a GeoJSON geometry mapping")
        return self


class OSITConfig(BaseModel):
    project_name: str = "OSIT Urban Network Assessment"
    area_of_interest: AreaOfInterest
    network_modes: list[NetworkMode] = Field(default_factory=lambda: ["drive", "walk"])
    analysis_profile: AnalysisProfile = "multimodal"
    travel_time_thresholds_minutes: list[int] = Field(default_factory=lambda: [5, 10, 15, 30, 45])
    points_of_interest: list[str] = Field(default_factory=list)
    output_crs: str = "auto_utm"
    data_currency_requirement: str = "record retrieval timestamp and OSM snapshot metadata"
    max_area_km2: float = Field(default=5000.0, gt=0, le=100_000)
    max_centrality_nodes: int = Field(default=7500, ge=100, le=100_000)
    cache_dir: Path = Path("data/cache")
    output_dir: Path = Path("outputs")

    @field_validator("network_modes")
    @classmethod
    def unique_modes(cls, value: list[NetworkMode]) -> list[NetworkMode]:
        if not value:
            raise ValueError("at least one network mode is required")
        return list(dict.fromkeys(value))

    @field_validator("travel_time_thresholds_minutes")
    @classmethod
    def valid_thresholds(cls, value: list[int]) -> list[int]:
        if not value or any(v <= 0 or v > 240 for v in value):
            raise ValueError("travel-time thresholds must be between 1 and 240 minutes")
        return sorted(set(value))


def load_config(path: str | Path) -> OSITConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a YAML mapping")
    return OSITConfig.model_validate(raw)
