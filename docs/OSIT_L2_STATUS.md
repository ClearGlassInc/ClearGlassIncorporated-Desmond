# OSIT L2 Draft Status

## Status

**L2 draft ready**

This iteration establishes a production-oriented design baseline for the Open Source Intelligence Toolkit (OSIT) analysis pipeline.

## Implemented Design Controls

- Model-level AOI validation instead of field-order dependent validation.
- Invalid geometry rejection by default; geometry repair requires explicit policy and audit evidence.
- CRS selection strategy using UTM only when suitable and local metric fallback otherwise.
- Deterministic provenance hashing based on canonicalized representations.
- Separate acquisition paths for drive, walk, bike, and rail layers.
- Rail preserved as a distinct feature layer until routing/linking requirements are validated.
- Connected components retained and annotated instead of silently discarded.
- OSMnx runtime settings and versions recorded in provenance.

## Operational Requirements

- Cache external data acquisition.
- Record retrieval timestamps, source licenses, query parameters, CRS, versions, and dataset hashes.
- Treat OpenStreetMap-derived attributes as community-maintained data requiring verification.
- Keep external-impact actions authorization controlled and auditable.

## Validation Targets

- AOI validation tests.
- Deterministic provenance hash tests.
- Multi-mode acquisition tests.
- Component preservation tests.
- Reproducible bounded analysis runs.

## Next Implementation Phase

Add the OSIT package modules, CI validation gates, analysis configuration, and reproducible fixture tests in a dedicated implementation branch before production merge.
