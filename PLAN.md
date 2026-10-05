# SafeCruise — Plan

Living plan: what gets built, in which order, and where it stands. The source of truth
for scope and design is the project brief (not published in this repository);
decisions that refine or change the brief are recorded as ADRs in
[docs/decisions/](docs/decisions/). Setup decisions from the pre-M0 review:
[ADR-000](docs/decisions/ADR-000-project-setup.md).

Status: **M1 in review** (branch `m1-hara`). Nothing in this repo is a result yet.

> **Next session starts here:** M1 is complete and approved; the PR waits for pb's merge
> and the `m1` tag. Then M2 (requirements and safety concepts) starts on `m2-requirements`.

---

## 1. Budget

- Core (M0–M7): **20–25 working days** (the brief's 13–15 days is treated as optimistic).
- M8 (HIL-lite) and all stretch items: only after M7 is merged.
- **Early showable cut-off:** M0–M4 plus a working SIL-lib.

## 2. Milestones

| M | Title | Status | Tag | Notes |
|---|---|---|---|---|
| M0 | Scaffold and feasibility spikes | done | `m0` | Docker image, CI skeleton, ADR-001 (SysML spike), ADR-002 (vcan spike) |
| M1 | Item definition, HARA, safety goals | in review | — | **pb authors** all ratings; ADR-003 HARA scope |
| M2 | Requirements and safety concepts | not started | — | EARS lint, trace gate v1, decomposition ADR |
| M3 | SysML v2 architecture | not started | — | |
| M4 | MIL | not started | — | Gain tuning ADR, FTTI experiment ADR (criterion written **before** the run) |
| M5 | Software requirements and embedded C | not started | — | |
| M6 | SIL, back-to-back, fault injection | not started | — | Trace gate strict |
| M7 | Verification report, safety case, ASPICE mapping, README | not started | — | |
| M8 | HIL-lite (optional) | deferred | — | Hardware bought near project end |

A milestone is done only when its *Done when* check (brief §12) holds, the evidence is in
the PR description, **pb has merged the PR**, and no requirement with ASIL ≥ A is still
`draft`.

## 3. Workflow

- Protected `main`. One branch and one PR per milestone (`m0-scaffold`, `m1-hara`, …).
  pb reviews and merges. Tag `m0`, `m1`, … after each merge.
- Required CI jobs: `build-unit` · `static-analysis` · `mil` · `sil-lib` · `sil-vecu` ·
  `docs-trace-gate` (placeholders until their milestone). GitHub Pages deploys from
  `main` only.
- One pinned Docker image serves as devcontainer and CI runner.

## 4. If time runs short

Cut depth, not areas. Trim in this order (first cut first):

1. SIL-vECU reduced to 1–2 integration scenarios (SIL-lib keeps all 14).
2. SysML v2 CI parsing replaced by a text-level ID consistency check (ADR-001 fallback).
3. RTE generator replaced by hand-written `Rte_*.h`; YAML kept as documentation.
4. MC/DC dropped; branch coverage only.
5. Safety case reduced to one fully worked GSN argument for the highest-ASIL safety goal.

**Never cut:** pb's HARA · EARS requirements with the trace gate · doer/checker with
scenario 14 · MIL + SIL-lib with B2B · unit tests and coverage on `AccMon` and E2E.

## 5. Values pb still owes

Placeholders appear in requirement drafts as `⟨pb: …⟩`; the EARS linter fails on any
that remain.

| Value | Needed by | Status |
|---|---|---|
| S/E/C ratings with rationale, ASIL per hazardous event | M1 | agreed, approval open |
| Safety goals: safe state (initial proposal in brief §5.4), FTTI | M1 | agreed, approval open |
| FTTI hazard criterion and assumed FTTI (before the MIL run) | M4 | open |
| TTC threshold for checker rule 2 | M2 | open |
| `AccMon` block hold time `T_hold` | M2 | open |
| Plausibility jump limits (checker rule 4) | M2 | open |
| E2E consecutive-error count (default 3) | M2 | open |
| ASIL of `TgtSel` and the decomposition of `AccCtrl` / `AccMon` | M2 | open |

## 6. Environment facts (checked 2026-09-29, updated 2026-10-06)

- Host: Ubuntu 24.04, GCC 13.3, Python 3.12.3, Java 21, Docker 29.1 (user in `docker` group).
- `vcan` kernel module present on the host (not loaded).
- Not installed on host: cmake, cppcheck, jupyter, arm-none-eabi-gcc. All go into the
  Docker image (with GCC 14) instead.
- Git repository on GitHub: https://github.com/Prennoy99/safecruise (public). `main` is
  protected by a ruleset; all work goes through a milestone branch and PR.
- Docker's default bridge network on this host cannot reach GitHub release assets (TLS
  connect times out; host networking works). Build locally with
  `docker build --network=host`; the devcontainer already passes it. CI is unaffected.
- GitHub CLI (`gh`) not installed; pb does GitHub-side steps in the browser. CI step logs
  need admin rights; without `gh`, results are read from the public API and the run's job
  summary.

## 7. M0 checklist

Brief §12 M0, refined by ADR-000. Items marked **(pb)** need pb to act.

**Repository**
- [x] `git init`, default branch `main`, work on branch `m0-scaffold` **(pb)**
- [x] `.gitignore` (at least `build/`, Python caches, docs build output, coverage output)
- [x] Public GitHub repo `safecruise` created **(pb)**, or via `gh` if authenticated;
      branch protection on `main` with the six required checks **(pb)** — ruleset active
- [x] README skeleton with the "in progress — design and intent only, no results" banner
      and the non-goals from brief §2

**Toolchain (D-08, D-20)**
- [x] `Dockerfile`: GCC 14, CMake ≥ 3.21, cppcheck + MISRA addon, lizard, gcovr,
      clang-format, Python 3.12, Java + SysML v2 Pilot Implementation (Jupyter kernel)
- [x] `.devcontainer/devcontainer.json` pointing at the `Dockerfile`
- [x] `pyproject.toml` with locked dependencies (sphinx, sphinx-needs,
      sphinx-test-reports, cantools, python-can, numpy, matplotlib, pytest, ruff, pyyaml)
      — `uv.lock`; also myst-parser (Markdown ADRs in the docs), lizard, gcovr, jupyter-client
- [x] Image built in CI and referenced by digest — `image` job pushes to GHCR, other jobs
      use `image@digest` (run #1)

**Build and tests**
- [x] `CMakeLists.txt` + `CMakePresets.json` pinned to GCC 14; warnings
      `-Wall -Wextra -Werror -pedantic -Wdouble-promotion -Wfloat-conversion`;
      `-ffast-math` explicitly absent (D-12) — configure fails on forbidden float flags
- [x] Empty SWC builds on host; Unity wired into CTest; `ctest --output-junit` works
- [x] pytest with `--junitxml`; `conftest.py` hook for `@pytest.mark.tc` → JUnit property (D-18)
- [x] ruff and clang-format configs
- [x] Repo directory layout from brief §10 (placeholders where empty)

**Docs**
- [x] Sphinx + sphinx-needs with need types (§6.1), link types, attributes
      (`asil`, `status: draft|approved`, `verification_method`, `safe_state`, `ftti_ms`,
      `level`)
- [x] `sphinx-build -b needs` produces `needs.json`; HTML builds

**Spikes**
- [x] Spike 1: SysML v2 Pilot parses a toy model in CI → **ADR-001** (fallback: text-level
      ID check in CI) — parses in CI; fallback not needed
- [x] Spike 2: `vcan` on the GitHub Actions runner + container with `--network=host` →
      **ADR-002** (fallback: UDP CanIf backend in CI) — works in CI; vcan chosen

**CI**
- [x] `.github/workflows/ci.yml` with jobs `build-unit`, `static-analysis`, `mil`,
      `sil-lib`, `sil-vecu`, `docs-trace-gate` (placeholders allowed); Pages deploy from
      `main` only

**(pb) before the first CI run:** enable GitHub Pages with source "GitHub Actions"; after
the first run, add the six jobs as required checks on `main`.

**Notes carried forward**
- CTest's JUnit output has one `<testcase>` per test *executable*; Unity function names
  (`test_TC_…`) appear only in `<system-out>`. The trace gate (M2/M6) must parse Unity's
  output lines, or each Unity test must be registered as its own CTest test. Decide by ADR
  in M5.
- sphinx-needs does not check that an ID's prefix matches its directive (`.. sys::` with
  `:id: TC_…` builds). `ears_lint.py` (M2) must check this.

**Done when:** CI is green; `sphinx-build` produces HTML and `needs.json`; ADR-001 and
ADR-002 are recorded; evidence is in the M0 PR; pb merges and tags `m0`.

M0 closed 2026-10-06: PR #1 merged as `740627e`, tagged `m0`, `main` CI green, Pages live
at https://prennoy99.github.io/safecruise/, ruleset on `main` (PR required, six checks,
no force push, no deletion).

## 8. M1 plan

Brief §12 M1, refined by ADR-000 D-04, D-05, D-17. Branch `m1-hara`. Items marked **(pb)**
are pb's alone; the rest is drafting that pb reviews.

- [x] PLAN.md: M1 in progress (first commit on the branch)
- [x] `00_item_definition.rst`: function, item boundary (brief §4.1), interfaces,
      operating modes, legal and functional constraints, known limitations; controllability
      depends on the D-04 assumptions (TOR display, actuator execution, brake-signal
      integrity, radar plausibility). Drafted; **pb reviews**
- [x] **ADR-003** HARA scope, accepted by pb: OS1 × M3 pruned; M3 widened to cover
      insufficient deceleration and wrong mode display; unintended activation within
      M1/M2; actuator capability (+3 / −8 m/s²) assumed, no actuator limit credited
- [x] **ADR-004** accepted: hazardous events as `HE_` needs, safety goals link to them,
      `tools/hara_check.py` checks them; runs in `docs-trace-gate`
- [x] `01_hara.rst` template: 19 hazardous events with `⟨pb: …⟩` for S, E, C, the
      rationale of each rating and the ASIL; HARA conventions decided by pb (malfunction
      magnitude, driver, exposure basis, severity guide)
- [x] `02_safety_goals.rst`: `SG_ACC_001`–`004` (one per malfunction), wording agreed,
      with `⟨pb: …⟩` for ASIL, safe state (per goal) and FTTI (initial; revisited after
      the M4 experiment)
- [x] ASIL check: `tools/hara_check.py` + `tests/tools/test_hara_check.py`; every ASIL
      matches the S/E/C risk table; fails while any `⟨pb: …⟩` remains (CI step, ADR-004)
- [x] All S/E/C ratings with rationale, ASILs; safe states, FTTIs (agreed by pb).
      Goals: `SG_ACC_001` B / 1000 ms, `002` C / 500 ms, `003` B / 1000 ms,
      `004` B / 500 ms
- [x] Review pass: arithmetic checked by `hara_check.py`; worked numbers in the reasons
      recomputed; no duplicate cells. Most sensitive ratings: `HE_OS2_M2` C3 (rests on the
      −8 m/s² magnitude; C2 with an actuator limit, which would make `SG_ACC_002` B) and
      `HE_OS5_M3` E3 (E4 with daily queue commuting, giving ASIL A)
- [x] **(pb)** review and set `status: approved` on every `HE_` and `SG_`

The HARA check step in `docs-trace-gate` fails on any value still open; its job summary
lists them. The step runs under `shell: bash`: the container's default `sh` has no
`pipefail`, which failed the first M1 CI run before the check ran.

**Done when:** `01_hara.rst` and `02_safety_goals.rst` build; every hazardous event has
S/E/C with rationale; every ASIL matches the risk table (test); each safety goal has a safe
state and FTTI; ADR-003 recorded; CI green; pb merges and tags `m1`.
