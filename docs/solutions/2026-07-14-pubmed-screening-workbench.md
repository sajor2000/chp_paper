# PubMed screening workbench

## Problem

Gate 2 had a reproducible PubMed universe but no controlled way to hand 1,178
records to investigators for screening without conflating a work queue with
completed review.

## Evidence

The frozen 2026-07-14 PubMed snapshot contains 1,178 records and 1,178 matching
screening rows, all pending investigator review. The literature protocol
requires title/abstract decisions before material novelty or comparator claims
can advance.

## Decision

Add `chicagohealthmap evidence screening build` to create deterministic batch
CSVs and an index from the frozen PubMed artifacts. Add
`chicagohealthmap evidence screening validate` to fail closed on malformed,
duplicated, unknown, or invalid screening rows while preserving
`gate_status: open`.

## Rejected alternatives

- Marking the existing queue as screened: rejected because no investigator
  decisions have been made.
- Writing reviewed decisions into the frozen source files: rejected because the
  source snapshot should remain immutable.
- Building the analytic dataset before screening: rejected because Gate 2 and
  later S4-S6 prerequisites remain open.

## Verification

Tests cover deterministic batch creation, overwrite refusal, draft validation,
complete-validation failure on blank decisions, duplicate and unknown PMID
rejection, invalid decision rejection, exclusion-reason enforcement, and CLI
build/validate behavior.

## Reusable pattern

When a scientific gate needs human review, generate a separate reviewer
workbench with immutable source reconciliation and a validator that reports
progress without advancing authority.
