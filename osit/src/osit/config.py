from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

import shapely.wkt
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import Polygon, box, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

NetworkMode = Literal["drive", "walk", "bike", "transit_rail"]
AnalysisProfile = Literal[
    "mobility", "accessibility", "resilience", "urban_morphology", "multimodal"
]
AoiMode = Literal["place_name", "bbox", "polygon", "geojson"]

BBox = Annotated[
    list[float],
    Field(min_length=4, max_length=4, description="[south, west, north, east] in WGS84"),
]


class AreaOfInterest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: AoiMode
    value: str | BBox | dict[str, Any] | list[Any]

    @model_validator(mode="after")
    def validate_value_for_mode(self) -> "AreaOfInterest":
        match self.mode:
            case "place_name":
                if not isinstance(self.value, str) or len(self.value.strip()) < 3:
                    raise ValueError("place_name requires a non-empty, specific place string")
            case "bbox":
                if not isinstance(self.value, list) or len(self.value) != 4:
                    raise ValueError("bbox requires [south, west, north, east]")
                south, west, north, east = self.value
                if not (-90 <= south < north <= 90):
                    raise ValueError("bbox latitude values must satisfy -90 <= south < north <= 90")
                if not (-180 <= west < east <= 180):
                    raise ValueError(
                        "bbox longitude values must satisfy -180 <= west < east <= 180; "
                        "antimeridian-crossing AOIs must use a polygon"
                    )
            case "polygon":
                geometry = self._geometry_from_polygon_value(self.value)
                self._validate_geometry_structure(geometry)
            case "geojson":
                if not isinstance(self.value, dict):
                    raise ValueError("geojson requires a GeoJSON geometry mapping")
                self._validate_geometry_structure(shape(self.value))
        return self

    @staticmethod
    def _geometry_from_polygon_value(value: Any) -> BaseGeometry:
        if isinstance(value, str):
            try:
                return shapely.wkt.loads(value)
            except Exception as exc:
                raise ValueError("polygon WKT is malformed") from exc
        if isinstance(value, dict):
            return shape(value)
        if isinstance(value, list):
            try:
                return Polygon(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("polygon coordinates are malformed") from exc
        raise ValueError("polygon requires WKT, GeoJSON geometry, or coordinate pairs")

    @staticmethod
    def _validate_geometry_structure(geometry: BaseGeometry) -> None:
        if geometry.is_empty:
            raise ValueError("AOI geometry must not be empty")
        if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("AOI geometry must be a Polygon or MultiPolygon")
        min_x, min_y, max_x, max_y = geometry.bounds
        if not (-180 <= min_x <= max_x <= 180 and -90 <= min_y <= max_y <= 90):
            raise ValueError("AOI geometry coordinates must be WGS84 longitude/latitude")

    def to_geometry(self) -> BaseGeometry:
        match self.mode:
            case "bbox":
                south, west, north, east = self.value  # type: ignore[misc]
                return box(west, south, east, north)
            case "polygon":
                return self._geometry_from_polygon_value(self.value)
            case "geojson":
                return shape(self.value)  # type: ignore[arg-type]
            case "place_name":
                raise ValueError("place_name AOIs must be geocoded before geometry conversion")
        raise RuntimeError(f"Unhandled AOI mode: {self.mode}")


class OSITConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str = Field(min_length=3, max_length=120)
    area_of_interest: AreaOfInterest
    network_modes: list[NetworkMode] = Field(default_factory=lambda: ["drive", "walk"])
    analysis_profile: AnalysisProfile = "multimodal"
    travel_time_thresholds_minutes: list[int] = Field(default_factory=lambda: [5, 10, 15, 30, 45])
    points_of_interest: list[str] = Field(default_factory=list)
    output_crs: str = "auto_local_metric"
    retain_all_components: bool = True
    simplify_network: bool = True
    request_timeout_seconds: int = Field(default=180, ge=30, le=600)
    overpass_max_retries: int = Field(default=4, ge=0, le=8)
    overpass_url: str | None = None
    repair_invalid_aoi: bool = False
    cache_dir: Path = Path("data/cache")
    output_dir: Path = Path("outputs")
    data_currency_requirement: str = (
        "Record retrieval timestamp, OSMnx version, effective OSMnx settings, source license, "
        "query inputs, and deterministic dataset hashes."
    )
    max_area_km2: float = Field(default=5000.0, gt=0, le=100_000)
    max_centrality_nodes: int = Field(default=7500, ge=100, le=100_000)

    @model_validator(mode="after")
    def validate_analysis_settings(self) -> "OSITConfig":
        if not self.network_modes:
            raise ValueError("at least one network mode is required")
        if len(set(self.network_modes)) != len(self.network_modes):
            raise ValueError("network_modes must not contain duplicates")
        thresholds = self.travel_time_thresholds_minutes
        if not thresholds or any(value <= 0 or value > 240 for value in thresholds):
            raise ValueError("travel-time thresholds must be between 1 and 240 minutes")
        if thresholds != sorted(set(thresholds)):
            raise ValueError("travel-time thresholds must be unique and ascending")
        if self.area_of_interest.mode != "place_name":
            geometry = self.area_of_interest.to_geometry()
            if not geometry.is_valid and not self.repair_invalid_aoi:
                raise ValueError(
                    f"AOI geometry is invalid: {explain_validity(geometry)}; "
                    "set repair_invalid_aoi=true to allow an audited repair path"
                )
        return self


def load_config(path: str | Path) -> OSITConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a YAML mapping")
    return OSITConfig.model_validate(raw)
