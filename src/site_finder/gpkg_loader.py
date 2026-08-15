"""Read the local South Australian parcel GeoPackage without GIS dependencies."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import BuildingEnvelope, Parcel, PlanningControls

DEFAULT_GPKG = Path(__file__).resolve().parents[2] / "data" / "parcels" / "sa-parcels.gpkg"
LAYER = "sa-parcels"


def dataset_info(path: Path = DEFAULT_GPKG) -> dict[str, object]:
    """Return basic metadata for the configured parcel dataset."""
    if not path.is_file():
        return {"connected": False, "path": str(path), "parcel_count": 0}
    with sqlite3.connect(path) as connection:
        count = connection.execute(f'SELECT COUNT(*) FROM "{LAYER}"').fetchone()[0]
    return {"connected": True, "name": path.name, "parcel_count": count, "crs": "EPSG:7854"}


def load_candidate_parcels(
    envelope: BuildingEnvelope, path: Path = DEFAULT_GPKG, limit: int = 100
) -> tuple[list[Parcel], int]:
    """Prefilter the GeoPackage and return model-ready candidate parcels."""
    if not path.is_file():
        raise FileNotFoundError(f"Parcel dataset not found: {path}")

    coverage_area = (
        envelope.footprint_sqm / envelope.maximum_design_site_coverage
        if envelope.maximum_design_site_coverage is not None
        else 0
    )
    minimum_area = max(envelope.minimum_site_area_sqm or 0, envelope.footprint_sqm, coverage_area)
    clauses = ["area_m2 >= ?", "COALESCE(restricted, 0) = 0"]
    parameters: list[object] = [minimum_area]
    clauses.append("(storeys IS NULL OR storeys >= ?)")
    parameters.append(envelope.storeys)
    if envelope.required_zone_codes:
        placeholders = ",".join("?" for _ in envelope.required_zone_codes)
        clauses.append(f"UPPER(est_zone) IN ({placeholders})")
        parameters.extend(envelope.required_zone_codes)
    zone_categories = envelope.required_zone_categories or envelope.assumptions.get(
        "zone_categories", []
    )
    if zone_categories:
        placeholders = ",".join("?" for _ in zone_categories)
        clauses.append(f"zone_category IN ({placeholders})")
        parameters.extend(zone_categories)

    where = " AND ".join(clauses)
    columns = "fid, area_m2, km_ring, est_zone, zone_category, storeys, min_lot, heritage"
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        total = connection.execute(
            f'SELECT COUNT(*) FROM "{LAYER}" WHERE {where}', parameters
        ).fetchone()[0]
        rows = connection.execute(
            f'SELECT {columns} FROM "{LAYER}" WHERE {where} '
            "ORDER BY area_m2 ASC, fid ASC LIMIT ?",
            [*parameters, max(1, min(limit, 500))],
        ).fetchall()

    parcels = []
    for row in rows:
        parcels.append(
            Parcel(
                parcel_id=str(row["fid"]),
                land_area_sqm=row["area_m2"],
                geometry_ref=f"{LAYER}:{row['fid']}",
                planning=PlanningControls(
                    zone_code=row["est_zone"] or "UNKNOWN",
                    zone_name=row["zone_category"] or row["est_zone"],
                    max_storeys=_optional_int(row["storeys"]),
                    min_site_area_sqm=row["min_lot"] if row["min_lot"] and row["min_lot"] > 0 else None,
                    overlays=["Heritage"] if row["heritage"] else [],
                    notes=f"Approximately {row['km_ring']} km from Adelaide CBD" if row["km_ring"] is not None else None,
                ),
            )
        )
    return parcels, total


def _optional_int(value: object) -> int | None:
    if value is None or float(value) <= 0:
        return None
    return max(1, round(float(value)))
