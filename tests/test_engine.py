from site_finder.engine import assess_parcel, find_candidate_sites
from site_finder.models import BuildingEnvelope, MatchStatus, Parcel, PlanningControls


def test_townhouse_candidate_passes_basic_controls():
    envelope = BuildingEnvelope(
        name="Townhouse",
        storeys=2,
        footprint_sqm=60,
        minimum_site_area_sqm=100,
        required_frontage_m=5,
        required_depth_m=16,
        required_zone_codes=["GN"],
    )
    parcel = Parcel(
        parcel_id="p1",
        land_area_sqm=125,
        frontage_m=6,
        depth_m=20,
        planning=PlanningControls(
            zone_code="gn",
            max_storeys=2,
            max_site_coverage=0.6,
            max_floor_area_ratio=1.1,
            min_site_area_sqm=100,
        ),
    )

    result = assess_parcel(parcel, envelope)

    assert result.status == MatchStatus.PASS
    assert result.score == 1


def test_parcels_are_sorted_with_passes_first():
    envelope = BuildingEnvelope(name="Apartment", storeys=6, footprint_sqm=130)
    passing = Parcel(
        parcel_id="pass",
        land_area_sqm=240,
        planning=PlanningControls(zone_code="UC", max_storeys=6, max_site_coverage=0.7),
    )
    failing = Parcel(
        parcel_id="fail",
        land_area_sqm=100,
        planning=PlanningControls(zone_code="GN", max_storeys=2, max_site_coverage=0.5),
    )

    results = find_candidate_sites([failing, passing], envelope)

    assert results[0].parcel.parcel_id == "pass"
    assert results[0].status in {MatchStatus.PASS, MatchStatus.REVIEW}
    assert results[-1].status == MatchStatus.FAIL
