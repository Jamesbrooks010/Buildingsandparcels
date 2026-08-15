# Project baseline

Baseline reviewed: 15 August 2026.

## Canonical code

- Repository: `Jamesbrooks010/Buildingsandparcels`.
- Starting branch: `codex/recover-site-finder` at `da78188`.
- The starting branch is the only substantive implementation branch; `main` contains only the repository initialization.
- The recovered branch and its local worktree were clean before this phase began.

## Current product

The application is an early Adelaide parcel-screening tool with three entry points: a Python API, a
command-line interface, and a dependency-free local web preview. It can load example JSON or query a
local South Australian parcel GeoPackage. The GeoPackage loader prefilters area, restriction status,
storeys, zone, and optional zone categories, then the engine produces explainable `pass`, `review`, or
`fail` outcomes.

The model currently separates:

- `BuildingEnvelope`: the proposed development's dimensions and allowed zones.
- `Parcel`: measured parcel area, frontage, depth, location fields, and attached controls.
- `PlanningControls`: structured limits that apply to the parcel.
- `RuleOutcome` / `ParcelAssessment`: rule-by-rule explanations and an aggregate screening status.

## Supported measurable checks

- Minimum site area, including subdivision/minimum-lot input.
- Allowed zone codes.
- Maximum storeys.
- Maximum site coverage ratio.
- Maximum floor-area ratio.
- Development-required frontage and depth.
- Planning minimum and maximum frontage.
- Front/rear and side setback fit when parcel and building dimensions are supplied.

Unknown controls or missing dimensions remain review items. The engine does not infer a compliant
building shape from footprint area alone.

## Known gaps

- The local GeoPackage does not currently supply measured frontage/depth or the new coverage, frontage,
  and setback controls. These checks become useful at scale only after a traceable spatial/rules join.
- The GeoPackage's `est_zone` column is entirely null. Connected screening therefore uses exact observed
  `zone_category` values, documented in `parcel-zone-data-contract.md`, without inferring zone codes.
- Parcel width/depth are simplified dimensions; irregular parcels need geometry-based buildable-area
  analysis in a later phase.
- No Planning Atlas rule corpus has been imported or interpreted.
- No market, transaction, approval, or built-outcome data is present.
- Results are screening evidence for professional review, not planning approval or advice.
