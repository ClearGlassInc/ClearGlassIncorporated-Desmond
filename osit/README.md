# OSIT — Open-Source Infrastructure Topology Intelligence

OSIT is ClearGlass Inc.'s reproducible, public-source geospatial and urban-network analytics module for mobility planning, accessibility research, resilience modeling, and urban morphology.

## Safety and analytical scope

OSIT uses openly licensed, public, non-personal data. It does not identify or profile people, and it does not provide targeting, evasion, disruption, or interference guidance. Structural outputs are deliberately labeled as **graph-model** results. A high-centrality segment, articulation point, graph bridge, or low-redundancy corridor is not automatically a real-world operationally critical asset.

OpenStreetMap is volunteered geographic information. Map completeness, tag completeness, topology, and freshness can differ from the physical world. Field validation and authoritative sources remain necessary for consequential planning decisions.

## Core capabilities

- AOI validation for place names, bounding boxes, polygons, and GeoJSON.
- Hard maximum-area controls to prevent accidental oversized public API queries.
- OSMnx/OpenStreetMap acquisition with local caching, retries, and provenance records.
- Drive, walk, bike, and public rail graph support.
- Projected graph processing and explicit estimated travel-time impedance.
- Topology, bounded centrality, articulation-point, bridge, and hypothetical edge-removal metrics.
- Network-constrained accessibility helpers.
- Street-orientation entropy/order metrics.
- GraphML, GeoPackage, GeoJSON, Parquet/CSV, JSON provenance, HTML, and Markdown export utilities.
- Deterministic tests and dedicated CI.

## Install

```bash
cd osit
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

Optional visualization/elevation extras:

```bash
pip install -e '.[visualization,elevation]'
```

## Validate configuration

```bash
osit validate --config config/analysis.yaml
```

Place-name mode intentionally requires a region/country qualifier to reduce ambiguous Nominatim resolutions.

## Run assessment

```bash
osit run --config config/analysis.yaml
```

The run performs AOI validation, resolves the public OSM geometry, acquires requested networks, projects them, adds disclosed travel-time estimates, computes bounded metrics, and writes outputs under `outputs/`.

Network acquisition requires internet access and remains subject to upstream OpenStreetMap/Nominatim/Overpass availability and usage policies. OSIT retries a failed public request three times and never substitutes another dataset silently.

## Test and lint

```bash
ruff check src tests
pytest --cov=osit --cov-report=term-missing
```

## Output structure

```text
outputs/
├── graphs/             # GraphML by mode + multimodal composition
├── tables/             # Parquet centrality tables and area summary JSON
├── reports/            # Markdown executive brief and HTML report
├── provenance/         # machine-readable source/artifact manifest
└── osit.gpkg           # primary geospatial deliverable
```

The implementation exposes GeoJSON export helpers for web-map pipelines. Public POIs, building footprints, GTFS, municipal open data, DEM, flood layers, and interactive Folium/MapLibre front ends are extension points; they must retain the same provenance and non-personal-data controls before being promoted to production.

## Source provenance

The core collector records each requested OSM network mode as a source with retrieval time, ODbL license, AOI/query parameters, CRS, and quality caveats. Generated artifacts receive SHA-256 checksums in the provenance manifest.

## Reproducibility notes

Dependency versions are pinned. Configuration is YAML and validated by Pydantic. Centrality computation is exact only below the configured node bound; above that bound OSIT uses seeded sampled betweenness and explicitly omits expensive exact closeness/eigenvector metrics rather than pretending they were computed.

## Security controls

- No embedded credentials or required secrets.
- No arbitrary user-supplied URL fetcher.
- Public OSM endpoints are accessed through OSMnx only.
- AOI sizes are bounded before acquisition.
- Place names must be geographically qualified.
- External network failures are surfaced, not hidden.
- Structured output/provenance avoids storing unnecessary raw source payloads.

## Label

Every generated report is labeled **OSIT — Open-Source Infrastructure Topology Intelligence**.
