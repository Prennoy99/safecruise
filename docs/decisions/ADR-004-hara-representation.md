# ADR-004 — Hazardous events as needs, checked against the ASIL table

- **Status:** accepted
- **Date:** 2026-10-06 (proposed and accepted)
- **Decided by:** pb
- **Relates to:** brief §6.1, §12 M1; [ADR-000](ADR-000-project-setup.md) D-17;
  [ADR-003](ADR-003-hara-scope.md)

## Context

M1 is done only when every hazardous event has S, E and C ratings with a written reason
each, every ASIL matches the risk table (checked by a test), and every safety goal has a
safe state and an FTTI. That needs the HARA in a form a tool can read. The need types of
brief §6.1 start at the safety goal; there is no type for a hazardous event, so the link
from a safety goal back to the events it covers would be prose only.

## Options

1. **HARA as a table in reStructuredText**, parsed by a script. Easy to read, but the
   parser depends on table layout, and safety goals cannot link to rows.
2. **HARA as a YAML file**, rendered into the docs by a custom directive and read by the
   check. Clean data, but one more file format and a custom Sphinx extension.
3. **A sphinx-needs type for hazardous events.** Ratings and reasons are need attributes,
   safety goals link to hazardous events with `derives_from`, and the check reads
   `needs.json`, the same export the trace gate (M2) uses.

## Decision

Option 3.

- New need type `he`, title "Hazardous event", prefix `HE_`. ID `HE_OS<n>_M<n>`, with an
  optional suffix when one cell needs more than one event (for example `HE_OS2_M1_WET`).
- Attributes: `situation`, `malfunction`, `severity`, `exposure`, `controllability`, one
  `…_rationale` per rating, `asil`, and `status` (draft | approved, ADR-000 D-17).
- A safety goal (`SG_`) links to the events it covers with `derives_from`.
- `tools/hara_check.py` reads `needs.json` and fails when:
  - a value pb owes is still a `⟨pb: …⟩` placeholder or empty (in needs, and in the prose
    of the M1 documents);
  - a rating is outside S0–S3, E0–E4, C0–C3, or the ASIL is not what the ratings give;
  - the situation or malfunction attribute does not match the ID;
  - an event with ASIL A or higher has no safety goal;
  - a safety goal links to no event, links to something other than an event, has an ASIL
    other than the highest of its events, or has an FTTI that is not a positive whole
    number of milliseconds.
- The ASIL table of ISO 26262-3 (clause 6) is implemented by its sum form (any class 0
  gives QM; S + E + C of 7, 8, 9, 10 gives A, B, C, D), so no table is copied. Unit tests
  in `tests/tools/test_hara_check.py` cover the corners and that the ASIL never drops when
  a class rises.
- CI runs the check in the `docs-trace-gate` job on the `needs.json` it has just built.

## Consequences

- `docs/conf.py` gains the `he` type and the HARA attributes; `test_needs_config.py`
  covers them.
- `docs-trace-gate` is red on the M1 branch until pb has filled in every rating, ASIL,
  safe state and FTTI. This is intended: the check's output is the list of what is still
  open.
- The trace gate (M2) can follow SG → HE links, for example to show which events each
  safety goal covers.
- A safety goal that covers only QM events is allowed by the check; whether it is kept is
  pb's decision.
