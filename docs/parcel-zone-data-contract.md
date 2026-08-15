# Parcel zone data contract

Audited against `data/parcels/sa-parcels.gpkg` on 15 August 2026.

## Observed fields

The `sa-parcels` layer contains 491,427 records. Its `est_zone` field is null for every record, so it
cannot currently support zone-code filters such as `GN`, `HDN`, or `UC`. The populated
`zone_category` field contains these exact values:

| Zone category | Parcels |
| --- | ---: |
| General Neighbourhood | 255,538 |
| Low-density neighbourhood | 119,274 |
| Higher density neighbourhood | 39,697 |
| Master Planned | 32,438 |
| Township/Rural | 23,165 |
| Mixed-use (non-CBD) | 8,324 |
| Activity Centre | 7,002 |
| CBD | 5,989 |

## Screening contract

- `required_zone_codes` compares only with a parcel's `zone_code`.
- `required_zone_categories` compares only with the exact `zone_name`/category value.
- The GeoPackage loader uses exact category values and returns `UNKNOWN` for its unavailable zone code.
- The application does not translate a category into a Planning and Design Code zone or infer a code.
- Missing or unknown zoning inputs remain visible and must not be treated as evidence of compliance.

The presets now use exact observed categories so connected screening can operate on the available data.
These categories are coarse screening classifications, not verified Planning Atlas rules. A future sourced
spatial join may populate authoritative zone/subzone identifiers alongside, rather than overwriting, this
field.

