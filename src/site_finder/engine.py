"""Rule-based parcel feasibility engine."""

from __future__ import annotations

from .models import BuildingEnvelope, MatchStatus, Parcel, ParcelAssessment, RuleOutcome


def assess_parcel(parcel: Parcel, envelope: BuildingEnvelope) -> ParcelAssessment:
    """Assess whether a building envelope is likely feasible on a parcel.

    The engine is intentionally conservative: hard rule failures fail the parcel, missing
    dimensional inputs create review items, and passing parcels are scored by usable capacity.
    """

    outcomes: list[RuleOutcome] = []
    planning = parcel.planning

    required_site_area = max(
        envelope.minimum_site_area_sqm or 0,
        planning.min_site_area_sqm or 0,
        envelope.footprint_sqm,
    )
    if parcel.land_area_sqm >= required_site_area:
        outcomes.append(_pass("site_area", f"{parcel.land_area_sqm:.0f} sqm meets {required_site_area:.0f} sqm minimum."))
    else:
        outcomes.append(_fail("site_area", f"{parcel.land_area_sqm:.0f} sqm is below {required_site_area:.0f} sqm minimum."))

    if envelope.maximum_design_site_coverage is not None:
        design_coverage = envelope.footprint_sqm / parcel.land_area_sqm
        if design_coverage <= envelope.maximum_design_site_coverage:
            outcomes.append(
                _pass(
                    "design_site_coverage",
                    f"Indicative design coverage {design_coverage:.0%} fits the scenario target "
                    f"of {envelope.maximum_design_site_coverage:.0%}.",
                )
            )
        else:
            outcomes.append(
                _fail(
                    "design_site_coverage",
                    f"Indicative design coverage {design_coverage:.0%} exceeds the scenario target "
                    f"of {envelope.maximum_design_site_coverage:.0%}.",
                )
            )

    if envelope.required_zone_codes:
        if planning.zone_code in envelope.required_zone_codes:
            outcomes.append(_pass("zone", f"Zone {planning.zone_code} is allowed."))
        else:
            outcomes.append(_fail("zone", f"Zone {planning.zone_code} is not in allowed zones: {', '.join(envelope.required_zone_codes)}."))

    if envelope.required_zone_categories:
        if planning.zone_name in envelope.required_zone_categories:
            outcomes.append(_pass("zone_category", f"Zone category {planning.zone_name} is allowed."))
        elif planning.zone_name is None:
            outcomes.append(_review("zone_category", "An allowed zone category is required, but the parcel category is missing."))
        else:
            outcomes.append(
                _fail(
                    "zone_category",
                    f"Zone category {planning.zone_name} is not allowed: "
                    f"{', '.join(envelope.required_zone_categories)}.",
                )
            )

    if planning.max_storeys is not None:
        if envelope.storeys <= planning.max_storeys:
            outcomes.append(_pass("storeys", f"{envelope.storeys} storeys fits {planning.max_storeys} storey control."))
        else:
            outcomes.append(_fail("storeys", f"{envelope.storeys} storeys exceeds {planning.max_storeys} storey control."))
    else:
        outcomes.append(_review("storeys", "No maximum storeys control supplied for this parcel."))

    if envelope.building_height_m is not None:
        if planning.max_building_height_m is None:
            outcomes.append(
                _review("building_height", "No maximum building-height control supplied for this parcel.")
            )
        elif envelope.building_height_m <= planning.max_building_height_m:
            outcomes.append(
                _pass(
                    "building_height",
                    f"Height {envelope.building_height_m:g}m fits the "
                    f"{planning.max_building_height_m:g}m control.",
                )
            )
        else:
            outcomes.append(
                _fail(
                    "building_height",
                    f"Height {envelope.building_height_m:g}m exceeds the "
                    f"{planning.max_building_height_m:g}m control.",
                )
            )

    if planning.max_site_coverage is not None:
        site_coverage = envelope.footprint_sqm / parcel.land_area_sqm
        if site_coverage <= planning.max_site_coverage:
            outcomes.append(_pass("site_coverage", f"Site coverage {site_coverage:.0%} fits {planning.max_site_coverage:.0%} control."))
        else:
            outcomes.append(_fail("site_coverage", f"Site coverage {site_coverage:.0%} exceeds {planning.max_site_coverage:.0%} control."))
    else:
        outcomes.append(_review("site_coverage", "No site coverage control supplied for this parcel."))

    if planning.max_floor_area_ratio is not None:
        floor_area_ratio = envelope.effective_gfa_sqm / parcel.land_area_sqm
        if floor_area_ratio <= planning.max_floor_area_ratio:
            outcomes.append(_pass("floor_area_ratio", f"FAR {floor_area_ratio:.2f} fits {planning.max_floor_area_ratio:.2f} control."))
        else:
            outcomes.append(_fail("floor_area_ratio", f"FAR {floor_area_ratio:.2f} exceeds {planning.max_floor_area_ratio:.2f} control."))
    else:
        outcomes.append(_review("floor_area_ratio", "No floor-area-ratio control supplied for this parcel."))

    _dimension_check(
        outcomes, "development_frontage", parcel.frontage_m, envelope.required_frontage_m, "m"
    )
    _dimension_check(outcomes, "depth", parcel.depth_m, envelope.required_depth_m, "m")
    _planning_frontage_checks(outcomes, parcel)
    _setback_checks(outcomes, parcel, envelope)

    status = _aggregate_status(outcomes)
    return ParcelAssessment(parcel=parcel, status=status, score=_score(outcomes), outcomes=outcomes)


def find_candidate_sites(parcels: list[Parcel], envelope: BuildingEnvelope) -> list[ParcelAssessment]:
    """Return parcel assessments sorted with strongest candidates first."""

    assessments = [assess_parcel(parcel, envelope) for parcel in parcels]
    return sorted(assessments, key=lambda item: (item.status != MatchStatus.PASS, -item.score, item.parcel.parcel_id))


def _dimension_check(
    outcomes: list[RuleOutcome], rule: str, actual: float | None, required: float, unit: str
) -> None:
    if required <= 0:
        return
    if actual is None:
        outcomes.append(_review(rule, f"Required {rule} is {required:g}{unit}, but parcel {rule} is missing."))
    elif actual >= required:
        outcomes.append(_pass(rule, f"{rule.title()} {actual:g}{unit} meets {required:g}{unit} requirement."))
    else:
        outcomes.append(_fail(rule, f"{rule.title()} {actual:g}{unit} is below {required:g}{unit} requirement."))


def _planning_frontage_checks(outcomes: list[RuleOutcome], parcel: Parcel) -> None:
    planning = parcel.planning
    controls = (
        ("planning_frontage_min", planning.min_frontage_m, "minimum", lambda actual, limit: actual >= limit),
        ("planning_frontage_max", planning.max_frontage_m, "maximum", lambda actual, limit: actual <= limit),
    )
    for rule, limit, label, comparison in controls:
        if limit is None:
            continue
        if parcel.frontage_m is None:
            outcomes.append(_review(rule, f"The {label} frontage is {limit:g}m, but parcel frontage is missing."))
        elif comparison(parcel.frontage_m, limit):
            outcomes.append(_pass(rule, f"Frontage {parcel.frontage_m:g}m meets the {label} {limit:g}m control."))
        else:
            outcomes.append(_fail(rule, f"Frontage {parcel.frontage_m:g}m breaches the {label} {limit:g}m control."))


def _setback_checks(
    outcomes: list[RuleOutcome], parcel: Parcel, envelope: BuildingEnvelope
) -> None:
    planning = parcel.planning
    front = planning.min_front_setback_m
    rear = planning.min_rear_setback_m
    side = planning.min_side_setback_m
    if front is None and rear is None and side is None:
        return

    if side is not None:
        required_width = None if envelope.building_width_m is None else envelope.building_width_m + 2 * side
        _fit_check(outcomes, "side_setbacks", parcel.frontage_m, required_width, "frontage", "building width")

    if front is not None or rear is not None:
        required_depth = (
            None
            if envelope.building_depth_m is None
            else envelope.building_depth_m + (front or 0) + (rear or 0)
        )
        _fit_check(outcomes, "front_rear_setbacks", parcel.depth_m, required_depth, "depth", "building depth")


def _fit_check(
    outcomes: list[RuleOutcome], rule: str, available: float | None, required: float | None,
    parcel_dimension: str, building_dimension: str,
) -> None:
    if required is None:
        outcomes.append(_review(rule, f"A setback control applies, but {building_dimension} is missing."))
    elif available is None:
        outcomes.append(_review(rule, f"Setbacks require {required:g}m, but parcel {parcel_dimension} is missing."))
    elif available >= required:
        outcomes.append(_pass(rule, f"Parcel {parcel_dimension} {available:g}m provides the required {required:g}m envelope."))
    else:
        outcomes.append(_fail(rule, f"Parcel {parcel_dimension} {available:g}m is below the required {required:g}m envelope."))


def _aggregate_status(outcomes: list[RuleOutcome]) -> MatchStatus:
    if any(outcome.status == MatchStatus.FAIL for outcome in outcomes):
        return MatchStatus.FAIL
    if any(outcome.status == MatchStatus.REVIEW for outcome in outcomes):
        return MatchStatus.REVIEW
    return MatchStatus.PASS


def _score(outcomes: list[RuleOutcome]) -> float:
    if not outcomes:
        return 0
    points = {MatchStatus.PASS: 1.0, MatchStatus.REVIEW: 0.5, MatchStatus.FAIL: 0.0}
    return round(sum(points[outcome.status] for outcome in outcomes) / len(outcomes), 3)


def _pass(rule: str, message: str) -> RuleOutcome:
    return RuleOutcome(rule=rule, status=MatchStatus.PASS, message=message)


def _review(rule: str, message: str) -> RuleOutcome:
    return RuleOutcome(rule=rule, status=MatchStatus.REVIEW, message=message)


def _fail(rule: str, message: str) -> RuleOutcome:
    return RuleOutcome(rule=rule, status=MatchStatus.FAIL, message=message)
