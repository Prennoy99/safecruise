# ADR-005 — EARS lint and trace gate v1

- **Status:** proposed
- **Date:** 2026-10-06 (proposed)
- **Decided by:** pb
- **Relates to:** brief §6.2, §6.3, §12 M2; [ADR-000](ADR-000-project-setup.md) D-17, D-18;
  [ADR-004](ADR-004-hara-representation.md)

## Context

M2 needs a requirement-quality linter and a first trace gate in CI. Brief §6.2 and §6.3 give
the rules in outline only; several details need a decision: what counts as a statement,
how "a number with a unit" is checked, which links are allowed between which need types,
how ASIL inheritance is checked, and which rules wait for test results (M6). M0 also noted
that sphinx-needs does not check that an ID prefix matches its directive.

## Options

1. **Check inside Sphinx** (custom extension or sphinx-needs warnings). Fails the docs build
   directly, but mixes checking with rendering and is harder to test on its own.
2. **Standalone tools on `needs.json`**, like `tools/hara_check.py` (ADR-004). One export,
   several small checks, each unit-tested on fixture data.

## Decision

Option 2: `tools/ears_lint.py` and `tools/trace_check.py`, both reading the `needs.json`
built in the `docs-trace-gate` job.

**EARS lint** (requirements are needs of type SYS, FSR, TSR, AOU, SWR):

- The statement is the first paragraph of the need's content, with inline markup removed.
  Later paragraphs (rationale, notes) are not linted.
- It matches one EARS template (ubiquitous, while, when, where, if … then, or a mix of
  while/when/where clauses) and contains exactly one "shall".
- It contains no vague word from a fixed list (for example "fast", "appropriate",
  "sufficient", "immediately", "about", "etc", "and/or").
- Every number carries a unit (ms, s, m, km/h, m/s, m/s², m/s³, %, Hz, or a counted noun
  such as cycles, frames, messages), or is part of a list whose last number does
  ("1.0, 1.5 or 2.0 s"). IDs and names such as `A-04`, `SG_ACC_001`, `E2E`, `CRC-8` are not
  numbers.
- Attributes: `asil` on every requirement (QM, A–D, or decomposed such as `B(D)`);
  `verification_method` (test, analysis, inspection, review) on SYS, FSR, TSR, SWR.
- On every need: the ID prefix matches the directive, and no field holds a `⟨pb: …⟩`
  placeholder (D-17).

**Trace gate v1:**

| From | Link | Allowed targets |
|---|---|---|
| SG | derives_from | HE |
| SYS | satisfies | STK |
| FSR | derives_from | SG |
| TSR | derives_from | FSR |
| AOU | derives_from | FSR, SYS |
| SWR | derives_from | SYS, TSR |
| SYS, FSR, TSR, SWR | allocated_to | ARC |
| TC | verifies | SYS, FSR, TSR, AOU, SWR |

- Errors: a dangling link or a link to a disallowed type; a safety goal without an FSR; an
  FSR without a TSR or AOU; a TSR without an allocation; a SYS that satisfies no STK.
- ASIL inheritance (error): an FSR, TSR or AOU has the same *target* ASIL as the highest of
  its parents. The target ASIL of a decomposed requirement is the part in brackets, so
  `B(D)` and `QM(D)` both inherit from a D parent.
- Warnings until M6, errors with `--strict`: a SYS, TSR or SWR without a test case; a need
  with ASIL A or higher that is still `draft`. JUnit results are added in M6.

**Diagrams:** `needflow` is rendered with Graphviz (`dot` added to the toolchain image)
instead of PlantUML, which would need a further Java tool and a Sphinx extension.

## Consequences

- `docs-trace-gate` runs EARS lint, trace gate and HARA check in that order; each writes its
  output to the job summary and each runs even if an earlier one failed.
- The trace gate fails on the M2 branch until every safety goal has its FSRs and every FSR
  its TSRs or AOUs.
- The lint is a heuristic: a statement can pass and still be a poor requirement. Review by
  pb remains the quality check; the lint catches form.
- M6 switches the trace gate to `--strict` and adds JUnit results (D-18).
