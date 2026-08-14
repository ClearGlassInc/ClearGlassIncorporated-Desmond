from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyproj import Geod
from shapely import make_valid
from shapely.geometry import Polygon, box, shape
from shapely.geometry.base import BaseGeometry

from .config import AreaOfInterest

WGS84 = Geod(ellps="WGS84")


class AOIValidationError(ValueError):
    """Raised when the requested area of interest is malformed or too large."""


@dataclass(frozen=True)
class AOIValidationResult:
    geometry: BaseGeometry | None
    area_km2: float | None
    notes: tuple[str, ...] = ()


def geodesic_area_km2(geometry: BaseGeometry) -> float:
    area_m2, _ = WGS84.geometry_area_perimeter(geometry)
    return abs(area_m2) / 1_000_000.0


def _polygon_from_coordinates(value: Any) -> BaseGeometry:
    if isinstance(value, dict):
        return shape(value)
    if not isinstance(value, list) or len(value) < 3:
        raise AOIValidationError("polygon must contain at least three coordinate pairs")
    return Polygon(value)


def validate_aoi(aoi: AreaOfInterest, max_area_km2: float) -> AOIValidationResult:
    if aoi.mode == "place_name":
        place = str(aoi.value).strip()
        if "," not in place:
            raise AOIValidationError(
                "ambiguous place_name rejected: include region/country, e.g. 'Burlington, Ontario, Canada'"
            )
        return AOIValidationResult(None, None, ("place geometry must be resolved before area validation",))

    if aoi.mode == "bbox":
        try:
            west, south, east, north = [float(v) for v in aoi.value]
        except (TypeError, ValueError) as exc:
            raise AOIValidationError("bbox values must be numeric") from exc
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise AOIValidationError("bbox must satisfy west < east and south < north in WGS84")
        geometry = box(west, south, east, north)
    elif aoi.mode == "geojson":
        geometry = shape(aoi.value)
    else:
        geometry = _polygon_from_coordinates(aoi.value)

    if geometry.is_empty:
        raise AOIValidationError("AOI geometry is empty")
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise AOIValidationError("AOI must resolve to a Polygon or MultiPolygon")
    if not geometry.is_valid:
        repaired = make_valid(geometry)
        if not repaired.is_valid or repaired.geom_type not in {"Polygon", "MultiPolygon"}:
            raise AOIValidationError("AOI polygon is invalid or self-intersecting")
        raise AOIValidationError("AOI polygon is invalid; provide a non-self-intersecting geometry")

    area_km2 = geodesic_area_km2(geometry)
    if area_km2 > max_area_km2:
        raise AOIValidationError(
            f"AOI is {area_km2:.1f} km², above configured maximum {max_area_km2:.1f} km²"
        )
    return AOIValidationResult(geometry, area_km2)


def validate_resolved_geometry(geometry: BaseGeometry, max_area_km2: float) -> float:
    if geometry.is_empty or not geometry.is_valid:
        raise AOIValidationError("resolved place geometry is empty or invalid")
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise AOIValidationError("resolved place must have polygonal boundary data")
    area_km2 = geodesic_area_km2(geometry)
    if area_km2 > max_area_km2:
        raise AOIValidationError(
            f"resolved AOI is {area_km2:.1f} km², above configured maximum {max_area_km2:.1f} km²"
        )
    return area_km2
