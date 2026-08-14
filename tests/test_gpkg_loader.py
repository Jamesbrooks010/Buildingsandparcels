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


def test_filters_mixed_use_categories():
    path = Path("data/parcels/sa-parcels.gpkg")
    if not path.exists():
        return
    envelope = BuildingEnvelope(
        name="Small mixed-use apartment",
        storeys=3,
        footprint_sqm=150,
        minimum_site_area_sqm=200,
        assumptions={"zone_categories": ["Mixed-use (non-CBD)", "Activity Centre", "CBD"]},
    )
    parcels, total = load_candidate_parcels(envelope, path=path, limit=10)
    assert total > 0
    assert all(
        parcel.planning.zone_name in {"Mixed-use (non-CBD)", "Activity Centre", "CBD"}
        for parcel in parcels
    )
