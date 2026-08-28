# S4 Chicago-frame position mapping

## Problem

The project needed to honor the investigator decision that the
ChicagoHealthMap website data dictionary is the authoritative S4 methods
dictionary, while also preserving the scientific distinction between the
broader CAPriCORN/ChicagoHealthMap source universe and the paper's Chicago case
studies.

## Evidence

- The official ChicagoHealthMap glossary snapshot defines the source methods:
  CAPriCORN clinical data, ACS denominator context, census tract primary
  geography, Chicago community-area aggregation, 2019-2024 time period,
  capture-rate reliability, and fewer-than-10 suppression.
- First-party source profiles show stable positional patterns for geography
  keys, year, condition labels, total condition counts, paired denominator-like
  and rate/proportion-like blocks, and reliability/capture crosswalks.
- Aggregate consistency checks identify the total diagnosed-condition count
  position in condition-stat tables without exposing row-level values.

## Decision

`docs/analysis/s4_methods_mapping.json` now records:

- six-county Chicagoland as the source provenance scope;
- City of Chicago as the case-study spatial frame;
- guarded core position mappings for geography, year, condition, numerator,
  paired denominator/rate blocks, source-published measure, capture rate, and
  reliability labels;
- guarded concepts for adult-denominator reconstruction, subgroup labels, and
  public fewer-than-10 suppression.

## Rejected alternatives

- Treating every raw field as semantically verified was rejected because the
  website glossary defines methods but not every subgroup export position.
- Treating the six-county source universe as the analytic map frame was rejected
  because the paper's case studies are within Chicago.
- Requiring new external documentation before recording any mapping was rejected
  because the investigator accepted the website dictionary as S4 authority and
  the raw source profiles support the core case-study fields.

## Verification

- `uv run pytest tests/unit/test_s4_dictionary.py -q`
- `uv run pytest tests/unit/test_s4_dictionary.py tests/unit/test_governance_readiness.py -q`

## Reusable pattern

Separate source scope from analytic spatial frame. A first-party source can have
a broader collection universe than the bounded case-study map. Record that
boundary in machine-readable governance artifacts before building analytic
datasets or notebooks.
