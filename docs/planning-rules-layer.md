# South Australian planning rules layer: proposed architecture

This document designs the next integration boundary. It does not claim that any Planning Atlas provision
has been encoded or that a parcel is compliant.

## Principles

1. Official planning material is the authority. Every extracted rule retains a direct source URL,
   document/version identifier, provision locator, effective date, and retrieval date.
2. Natural-language extraction proposes rules; it does not silently publish them. A reviewer accepts,
   corrects, or rejects each proposal.
3. The screening engine evaluates explicit typed rules. It does not use generated prose as a pass/fail
   control.
4. Conditional, qualitative, conflicting, missing, or stale material returns `review`, with the reason.
5. Source text snapshots and transformed rules are versioned so a result can be reproduced.

## Suggested records

### Source record

`source_id`, official URL, title, issuing authority, document/version, effective dates, retrieved timestamp,
content checksum, and local snapshot reference.

### Provision record

`provision_id`, `source_id`, exact locator (part/table/row/page or stable fragment), short source excerpt,
applicability text, and extraction notes. Excerpts should be kept only to the extent licensing permits.

### Rule record

`rule_id`, provision link, scope (zone/subzone/overlay/development type), typed control, operator, value,
unit, conditions, exceptions, interpretation status, confidence, reviewer, reviewed timestamp, and rule
version. Initial interpretation statuses should be:

- `draft_extracted`: machine-proposed and never used for a definitive pass.
- `needs_review`: ambiguity, qualitative judgment, missing applicability, or conflicting controls.
- `reviewed`: checked against the cited official provision and eligible for screening.
- `superseded`: retained for reproducibility but not used for current screening.

### Parcel applicability record

Links a parcel to zone, subzone, overlays, and other spatial scopes, with the spatial dataset source/version
and join method. This is separate from the rule itself so spatial and textual sources can be updated and
audited independently.

### Evaluation record

Stores parcel, development scenario, rule/version, inputs, result (`pass`, `fail`, or `review`), explanation,
and evaluation timestamp. A result with unreviewed rules, unresolved conflicts, or missing inputs must not
be promoted beyond `review`.

## Processing flow

1. Acquire and snapshot official sources; record version and checksum.
2. Segment sources into addressable provisions.
3. Extract candidate typed rules with provision citations and applicability.
4. Validate units, ranges, conflicting rules, and required conditions automatically.
5. Send candidates to a human review queue.
6. Publish reviewed rule versions to the deterministic feasibility engine.
7. Join current spatial applicability to parcels and retain source/version lineage.
8. Return rule-level evidence and review flags with every parcel result.

## Integration sequence

Start with a small, representative set of numeric controls already understood by the engine: site coverage,
minimum/maximum frontage, and setbacks. Validate the complete source-to-result audit trail on that slice
before expanding to height, site area, overlays, or qualitative desired outcomes. Market data should enter
through a separate later module keyed to stable parcel identifiers; it must not be mixed with planning-rule
authority or alter compliance outcomes.

## Product language

Use “screen”, “indicator”, “source-linked control”, and “planner review required”. Avoid “approved”,
“compliant”, or “developable” unless a qualified professional has made that determination outside the tool.

