# Roadmap

## Phase 1: MVP screening engine

- Accept a building type or explicit envelope assumptions.
- Load joined parcel and planning attributes from JSON.
- Return candidate sites with pass/review/fail rule outcomes.
- Provide both a local CLI and a small web API.

## Phase 2: Adelaide data ingestion

- Add importers for parcel boundaries and planning layers.
- Build repeatable spatial joins between parcels, zones, overlays, and constraints.
- Store processed data in a local GeoPackage or database.

## Phase 3: planner-grade feasibility

- Ingest source-linked, reviewed site coverage, frontage, and setback controls for a representative area.
- Add geometry-derived frontage and buildable-area analysis for irregular parcels.
- Add private open space, car parking, heritage/flood/tree overlays, and council-specific constraints.
- Add map output and downloadable candidate reports.
- Add scenario comparison for multiple building envelopes.

## Phase 4: market and outcome evidence

- Join market data through stable parcel identifiers without mixing it into planning-rule authority.
- Add land-rate and transaction indicators.
- Link approvals and built outcomes where reliable source data exists.
