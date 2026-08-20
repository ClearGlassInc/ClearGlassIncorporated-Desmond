import pytest

from osit.config import AreaOfInterest
from osit.validation import AOIValidationError, validate_aoi


def test_bbox_validates() -> None:
    result = validate_aoi(
        AreaOfInterest(mode="bbox", value=[-79.9, 43.2, -79.7, 43.4]),
        10_000,
    )
    assert result.geometry is not None
    assert result.area_km2 is not None
    assert result.area_km2 > 0


def test_bbox_rejects_bad_axis_order() -> None:
    with pytest.raises(AOIValidationError):
        validate_aoi(
            AreaOfInterest(mode="bbox", value=[-79.7, 43.2, -79.9, 43.4]),
            10_000,
        )


def test_place_name_requires_disambiguation() -> None:
    with pytest.raises(AOIValidationError, match="ambiguous"):
        validate_aoi(AreaOfInterest(mode="place_name", value="Burlington"), 10_000)


def test_oversized_request_is_rejected() -> None:
    with pytest.raises(AOIValidationError, match="above configured maximum"):
        validate_aoi(AreaOfInterest(mode="bbox", value=[-80, 42, -70, 50]), 1.0)


def test_geojson_requires_mapping() -> None:
    with pytest.raises(ValueError, match="GeoJSON geometry mapping"):
        AreaOfInterest(mode="geojson", value=[[0, 0], [1, 0], [1, 1]])


def test_malformed_geojson_is_normalized_to_aoi_error() -> None:
    aoi = AreaOfInterest(mode="geojson", value={"coordinates": []})
    with pytest.raises(AOIValidationError, match="geometry mapping is malformed"):
        validate_aoi(aoi, 10_000)


def test_self_intersecting_polygon_is_rejected() -> None:
    aoi = AreaOfInterest(
        mode="polygon",
        value=[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]],
    )
    with pytest.raises(AOIValidationError, match="non-self-intersecting"):
        validate_aoi(aoi, 10_000)
