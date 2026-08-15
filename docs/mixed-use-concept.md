# Indicative three-level mixed-use concept

This preset is a screening concept, not a statement of planning compliance or development suitability.
It represents ground-floor commercial space with two residential levels above.

## Design assumptions

| Input | Assumption | Treatment |
| --- | ---: | --- |
| Storeys | 3 | Compared with the GeoPackage's coarse storey field. |
| Approximate height | 11 m | Returns `review` unless a sourced maximum-height control exists. |
| Footprint | 180 sqm (12 m x 15 m) | Proposed building envelope only. |
| Gross floor area | 540 sqm | Used for FAR screening where a sourced control exists. |
| Minimum site area | 300 sqm | Scenario assumption. |
| Design coverage target | maximum 60% | Evaluated separately from the unknown planning coverage control. |
| Minimum frontage | 14 m | Allows a conceptual 12 m width plus 1 m each side; parcel frontage is currently missing. |
| Minimum depth | 24 m | Allows a conceptual 15 m depth plus 9 m total front/rear space; parcel depth is currently missing. |
| Categories | Mixed-use (non-CBD), Activity Centre, CBD | Exact coarse categories observed in the connected dataset. |

The frontage/depth allowances are not Planning Atlas setbacks. Authoritative land-use permission, height,
site coverage, setbacks, parking, vehicle access, overlays, interface requirements, and other provisions
have not been joined to the connected parcels. Those checks must remain `review` until official,
source-linked controls and parcel dimensions are available.

## Reproducing the screen

Start the preview, select **Mixed use**, retain **Connected parcel dataset**, and run the search. Expand a
result card to see every pass, fail, and review reason. The map plots the first 100 returned parcel-envelope
centres; selecting a marker opens its matching explanation. It does not display all coarse candidates or
authoritative parcel boundaries.
