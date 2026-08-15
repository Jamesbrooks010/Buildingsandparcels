"""Read the local South Australian parcel GeoPackage without GIS dependencies."""

from __future__ import annotations

import sqlite3
import struct
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
    columns = "fid, geom, area_m2, km_ring, est_zone, zone_category, storeys, min_lot, heritage"
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
        map_point = _gpkg_envelope_center(row["geom"])
        parcels.append(
            Parcel(
                parcel_id=str(row["fid"]),
                land_area_sqm=row["area_m2"],
                geometry_ref=f"{LAYER}:{row['fid']}",
                map_x=map_point[0] if map_point else None,
                map_y=map_point[1] if map_point else None,
                map_crs="EPSG:7854" if map_point else None,
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


def _gpkg_envelope_center(geometry: bytes | None) -> tuple[float, float] | None:
    """Return the centre of a GeoPackage XY envelope without inventing coordinates."""
    if geometry is None or len(geometry) < 40 or geometry[:2] != b"GP":
        return None
    flags = geometry[3]
    envelope_type = (flags >> 1) & 0b111
    if envelope_type == 0:
        return None
    endian = "<" if flags & 1 else ">"
    min_x, max_x, min_y, max_y = struct.unpack(f"{endian}dddd", geometry[8:40])
    return ((min_x + max_x) / 2, (min_y + max_y) / 2)
