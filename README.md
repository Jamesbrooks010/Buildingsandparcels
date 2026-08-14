# Adelaide Site Finder

A starter tool for finding Adelaide property parcels where a proposed building type or building envelope may be feasible. The repository is ready for parcel and planning datasets to be attached later; it currently includes a rule-based screening engine, a CLI, a FastAPI app, and example JSON inputs.

## What it does now

- Takes a building envelope such as a two-storey townhouse or six-level apartment.
- Assesses parcels against basic planning and dimensional controls.
- Returns candidate sites with `pass`, `review`, or `fail` rule outcomes.
- Reads the local `data/parcels/sa-parcels.gpkg` dataset when present, with sample files retained for tests and fallback development.

## Project structure

```text
src/site_finder/      Core Python package, API, CLI, models, and screening rules.
examples/             Example envelopes and sample parcel/planning records.
data/                 Placeholder folders for your local parcel and planning datasets.
docs/                 Product and implementation roadmap.
tests/                Regression tests for the screening engine.
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
site-finder --parcels examples/sample_parcels.json --envelope examples/envelope_townhouse.json
```

Run the web API:

```bash
uvicorn site_finder.api:app --reload
```

Or run the dependency-free visual preview (recommended while the real data is not attached):

```bash
site-finder-web
# Open http://127.0.0.1:8000
```

Then post a request to `POST /candidates` with this shape:

```json
{
  "envelope": { "name": "Two storey townhouse", "storeys": 2, "footprint_sqm": 60 },
  "parcels": [],
  "include_failures": false
}
```

## Adding Adelaide parcel and planning data

1. Pull this repository locally.
2. Add raw or processed parcel files under `data/parcels/`.
3. Add planning controls under `data/planning/`.
4. Join parcel IDs, land area, frontage/depth, zone, overlays, and planning controls into the JSON format shown in `examples/sample_parcels.json`.
5. Run the CLI or API against that JSON while we build richer GIS ingestion.

## Important limitations

This is an early screening tool, not a planning approval decision. Outputs should be treated as candidate leads for planner review until detailed controls, overlays, setbacks, site-specific geometry, and current South Australian planning rules are fully modelled.
