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


def test_setbacks_and_frontage_bounds_are_explicit_hard_checks():
    envelope = BuildingEnvelope(
        name="Townhouse",
        storeys=2,
        footprint_sqm=80,
        building_width_m=8,
        building_depth_m=10,
    )
    parcel = Parcel(
        parcel_id="setback-fit",
        land_area_sqm=300,
        frontage_m=12,
        depth_m=20,
        planning=PlanningControls(
            zone_code="GN",
            max_storeys=2,
            min_frontage_m=10,
            max_frontage_m=14,
            min_front_setback_m=4,
            min_rear_setback_m=3,
            min_side_setback_m=1.5,
        ),
    )

    result = assess_parcel(parcel, envelope)
    outcomes = {outcome.rule: outcome.status for outcome in result.outcomes}

    assert outcomes["planning_frontage_min"] == MatchStatus.PASS
    assert outcomes["planning_frontage_max"] == MatchStatus.PASS
    assert outcomes["side_setbacks"] == MatchStatus.PASS
    assert outcomes["front_rear_setbacks"] == MatchStatus.PASS


def test_missing_dimensions_trigger_review_instead_of_assumed_setback_fit():
    envelope = BuildingEnvelope(name="Apartment", storeys=3, footprint_sqm=120)
    parcel = Parcel(
        parcel_id="unknown-shape",
        land_area_sqm=500,
        planning=PlanningControls(
            zone_code="UC", max_storeys=4, min_front_setback_m=3, min_side_setback_m=1
        ),
    )

    result = assess_parcel(parcel, envelope)
    outcomes = {outcome.rule: outcome.status for outcome in result.outcomes}

    assert outcomes["side_setbacks"] == MatchStatus.REVIEW
    assert outcomes["front_rear_setbacks"] == MatchStatus.REVIEW


def test_invalid_frontage_range_is_rejected():
    try:
        PlanningControls(zone_code="GN", min_frontage_m=15, max_frontage_m=10)
    except ValueError as error:
        assert "min_frontage_m" in str(error)
    else:
        raise AssertionError("Expected an invalid frontage range to raise ValueError")
