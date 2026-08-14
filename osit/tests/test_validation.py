import pytest

from osit.config import AreaOfInterest
from osit.validation import AOIValidationError, validate_aoi


def test_bbox_validates() -> None:
    result = validate_aoi(AreaOfInterest(mode="bbox", value=[-79.9, 43.2, -79.7, 43.4]), 10_000)
    assert result.geometry is not None
    assert result.area_km2 is not None
    assert result.area_km2 > 0


def test_bbox_rejects_bad_axis_order() -> None:
    with pytest.raises(AOIValidationError):
        validate_aoi(AreaOfInterest(mode="bbox", value=[-79.7, 43.2, -79.9, 43.4]), 10_000)


def test_place_name_requires_disambiguation() -> None:
    with pytest.raises(AOIValidationError, match="ambiguous"):
        validate_aoi(AreaOfInterest(mode="place_name", value="Burlington"), 10_000)


def test_oversized_request_is_rejected() -> None:
    with pytest.raises(AOIValidationError, match="above configured maximum"):
        validate_aoi(AreaOfInterest(mode="bbox", value=[-80, 42, -70, 50]), 1.0)
