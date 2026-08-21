from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyproj import Geod
from shapely.errors import ShapelyError
from shapely.geometry import Polygon, box, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

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


def _polygon_value(value: Any) -> BaseGeometry:
    if isinstance(value, str):
        try:
            from shapely import wkt
            return wkt.loads(value)
        except Exception as exc:
            raise AOIValidationError("polygon WKT is malformed") from exc
    if isinstance(value, dict):
        try:
            return shape(value)
        except (AttributeError, KeyError, TypeError, ValueError, ShapelyError) as exc:
            raise AOIValidationError("polygon geometry mapping is malformed") from exc
    if isinstance(value, list):
        try:
            return Polygon(value)
        except (TypeError, ValueError, ShapelyError) as exc:
            raise AOIValidationError("polygon coordinates are malformed") from exc
    raise AOIValidationError("polygon must be WKT, GeoJSON geometry, or coordinate pairs")


def validate_aoi(
    aoi: AreaOfInterest,
    max_area_km2: float,
    repair_invalid: bool = False,
) -> AOIValidationResult:
    if aoi.mode == "place_name":
        place = str(aoi.value).strip()
        if len(place) < 3 or "," not in place:
            raise AOIValidationError(
                "ambiguous place_name rejected: include region/country, e.g. 'Burlington, Ontario, Canada'"
            )
        return AOIValidationResult(None, None, ("place geometry must be resolved before area validation",))

    if aoi.mode == "bbox":
        try:
            south, west, north, east = [float(v) for v in aoi.value]  # type: ignore[misc]
        except (TypeError, ValueError) as exc:
            raise AOIValidationError("bbox values must be numeric") from exc
        if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
            raise AOIValidationError("bbox must satisfy south < north and west < east in WGS84")
        geometry = box(west, south, east, north)
    elif aoi.mode == "polygon":
        geometry = _polygon_value(aoi.value)
    else:
        try:
            geometry = shape(aoi.value)
        except (AttributeError, KeyError, TypeError, ValueError, ShapelyError) as exc:
            raise AOIValidationError("geojson geometry mapping is malformed") from exc

    if geometry.is_empty:
        raise AOIValidationError("AOI geometry is empty")
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise AOIValidationError("AOI must resolve to a Polygon or MultiPolygon")
    min_x, min_y, max_x, max_y = geometry.bounds
    if not (-180 <= min_x <= max_x <= 180 and -90 <= min_y <= max_y <= 90):
        raise AOIValidationError("AOI coordinates must be WGS84 longitude/latitude")

    notes: list[str] = []
    if not geometry.is_valid:
        if not repair_invalid:
            raise AOIValidationError(
                f"AOI geometry is invalid: {explain_validity(geometry)}"
            )
        repaired = geometry.buffer(0)
        if repaired.is_empty or not repaired.is_valid:
            raise AOIValidationError("explicit AOI repair failed; original geometry was rejected")
        geometry = repaired
        notes.append(
            "AOI geometry repaired with buffer(0) under explicit configuration; repair recorded in provenance"
        )

    area_km2 = geodesic_area_km2(geometry)
    if area_km2 > max_area_km2:
        raise AOIValidationError(
            f"AOI is {area_km2:.1f} km², above configured maximum {max_area_km2:.1f} km²"
        )
    return AOIValidationResult(geometry, area_km2, tuple(notes))


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
