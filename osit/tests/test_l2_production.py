import geopandas as gpd
import pytest
from shapely.geometry import LineString

from osit.config import OSITConfig
from osit.network_builder import select_metric_crs
from osit.provenance import canonical_sha256


def test_rejects_invalid_bbox_order() -> None:
    invalid = {
        "project_name": "OSIT Test",
        "area_of_interest": {"mode": "bbox", "value": [43.9, -79.4, 43.7, -79.1]},
    }
    with pytest.raises(ValueError, match="latitude"):
        OSITConfig.model_validate(invalid)


def test_rejects_self_intersecting_polygon_by_default() -> None:
    invalid = {
        "project_name": "OSIT Test",
        "area_of_interest": {
            "mode": "polygon",
            "value": "POLYGON((0 0, 2 2, 0 2, 2 0, 0 0))",
        },
    }
    with pytest.raises(ValueError, match="invalid"):
        OSITConfig.model_validate(invalid)


def test_explicit_aoi_repair_requires_configuration() -> None:
    configured = {
        "project_name": "OSIT Test",
        "area_of_interest": {
            "mode": "polygon",
            "value": "POLYGON((0 0, 2 2, 0 2, 2 0, 0 0))",
        },
        "repair_invalid_aoi": True,
    }
    config = OSITConfig.model_validate(configured)
    assert config.repair_invalid_aoi is True


def test_canonical_hash_is_stable_across_row_and_column_order() -> None:
    first = gpd.GeoDataFrame(
        {"z": [2, 1], "a": ["beta", "alpha"]},
        geometry=[LineString([(0, 0), (1, 1)]), LineString([(2, 2), (3, 3)])],
        crs="EPSG:4326",
    )
    second = first[["a", "z", "geometry"]].iloc[[1, 0]].reset_index(drop=True)
    assert canonical_sha256(first) == canonical_sha256(second)


def test_metric_crs_falls_back_when_geometry_spans_multiple_utm_zones(monkeypatch) -> None:
    nodes = gpd.GeoDataFrame(
        {"node": [0], "geometry": [LineString([(-80, 43), (-70, 43)]).centroid]},
        geometry="geometry",
        crs="EPSG:4326",
    )

    import osit.network_builder as module

    monkeypatch.setattr(
        module.ox,
        "graph_to_gdfs",
        lambda graph, nodes=True, edges=False: (nodes, None),
    )
    crs = select_metric_crs(object())
    assert crs.to_dict().get("proj") == "aeqd"


def test_transit_rail_is_a_distinct_declared_mode() -> None:
    config = OSITConfig.model_validate(
        {
            "project_name": "OSIT Test",
            "area_of_interest": {"mode": "bbox", "value": [43.30, -79.90, 43.33, -79.82]},
            "network_modes": ["drive", "transit_rail"],
        }
    )
    assert "transit_rail" in config.network_modes
