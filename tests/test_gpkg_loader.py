from pathlib import Path

from site_finder.gpkg_loader import dataset_info, load_candidate_parcels
from site_finder.models import BuildingEnvelope


def test_reads_local_parcel_geopackage():
    path = Path("data/parcels/sa-parcels.gpkg")
    if not path.exists():
        return

    info = dataset_info(path)
    assert info["parcel_count"] == 491427

    envelope = BuildingEnvelope(name="Test", storeys=2, footprint_sqm=60)
    parcels, total = load_candidate_parcels(envelope, path=path, limit=3)
    assert total > 0
    assert len(parcels) == 3
    assert all(parcel.land_area_sqm >= 60 for parcel in parcels)
    assert all(parcel.map_crs == "EPSG:7854" for parcel in parcels)
    assert all(100_000 < parcel.map_x < 900_000 for parcel in parcels)
    assert all(5_000_000 < parcel.map_y < 8_000_000 for parcel in parcels)


def test_filters_mixed_use_categories():
    path = Path("data/parcels/sa-parcels.gpkg")
    if not path.exists():
        return
    envelope = BuildingEnvelope(
        name="Small mixed-use apartment",
        storeys=3,
        footprint_sqm=150,
        minimum_site_area_sqm=200,
        required_zone_categories=["Mixed-use (non-CBD)", "Activity Centre", "CBD"],
    )
    parcels, total = load_candidate_parcels(envelope, path=path, limit=10)
    assert total > 0
    assert all(
        parcel.planning.zone_name in {"Mixed-use (non-CBD)", "Activity Centre", "CBD"}
        for parcel in parcels
    )


def test_connected_townhouse_categories_return_candidates():
    path = Path("data/parcels/sa-parcels.gpkg")
    if not path.exists():
        return
    envelope = BuildingEnvelope(
        name="Townhouse category screen",
        storeys=2,
        footprint_sqm=60,
        minimum_site_area_sqm=100,
        required_zone_categories=["General Neighbourhood", "Higher density neighbourhood"],
    )

    parcels, total = load_candidate_parcels(envelope, path=path, limit=10)

    assert total > 0
    assert len(parcels) == 10
    assert all(parcel.planning.zone_code == "UNKNOWN" for parcel in parcels)
    assert all(parcel.planning.zone_name in envelope.required_zone_categories for parcel in parcels)
    assert all(parcel.map_x is not None and parcel.map_y is not None for parcel in parcels)


def test_connected_mixed_use_concept_returns_coarse_candidates():
    path = Path("data/parcels/sa-parcels.gpkg")
    if not path.exists():
        return
    envelope = BuildingEnvelope(
        name="Indicative mixed-use concept",
        storeys=3,
        footprint_sqm=180,
        building_height_m=11,
        minimum_site_area_sqm=300,
        required_zone_categories=["Mixed-use (non-CBD)", "Activity Centre", "CBD"],
    )

    parcels, total = load_candidate_parcels(envelope, path=path, limit=10)

    assert total > 0
    assert len(parcels) == 10
    assert all(parcel.planning.zone_name in envelope.required_zone_categories for parcel in parcels)
