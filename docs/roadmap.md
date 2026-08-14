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

- Add setbacks, private open space, car parking, heritage/flood/tree overlays, and council-specific constraints.
- Add map output and downloadable candidate reports.
- Add scenario comparison for multiple building envelopes.
