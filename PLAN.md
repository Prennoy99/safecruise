# SafeCruise — Plan

Living plan: what gets built, in which order, and where it stands. The source of truth
for scope and design is the project brief (not published in this repository);
decisions that refine or change the brief are recorded as ADRs in
[docs/decisions/](docs/decisions/). Setup decisions from the pre-M0 review:
[ADR-000](docs/decisions/ADR-000-project-setup.md).

Status: **M3 done (tag `m3`); M4 in progress** on branch `m4-mil`. Nothing in this
repo is a result yet.

> **Next session starts here:** M4 on branch `m4-mil`, plan in §11. ADR-010 (accepted)
> fixes both MIL experiments before the run and adds `AOU_ACC_011` (draft). Next: the
> simulation in `sim/`, then the reference controller.

---

## 1. Budget

- Core (M0–M7): **20–25 working days** (the brief's 13–15 days is treated as optimistic).
- M8 (HIL-lite) and all stretch items: only after M7 is merged.
- **Early showable cut-off:** M0–M4 plus a working SIL-lib.

## 2. Milestones

| M | Title | Status | Tag | Notes |
|---|---|---|---|---|
| M0 | Scaffold and feasibility spikes | done | `m0` | Docker image, CI skeleton, ADR-001 (SysML spike), ADR-002 (vcan spike) |
| M1 | Item definition, HARA, safety goals | done | `m1` | 19 hazardous events, 4 safety goals (B / C / B / B); ADR-003, ADR-004 |
| M2 | Requirements and safety concepts | done | `m2` | 7 `STK_`, 37 `SYS_`, 17 `FSR_`, 24 `TSR_`, 10 `AOU_`; EARS lint, trace gate v1; ADR-005 to ADR-008 |
| M3 | SysML v2 architecture | done | `m3` | Model, `sysml_check.py`, views in `07`; ADR-009 |
| M4 | MIL | in progress | — | ADR-010 experiments fixed before the run; gain tuning ADR |
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
| S/E/C ratings with rationale, ASIL per hazardous event | M1 | done (approved) |
| Safety goals: safe state (initial proposal in brief §5.4), FTTI | M1 | done (approved) |
| FTTI hazard criterion and assumed FTTI (before the MIL run) | M4 | done: time headway < 0.5 s, +3.0 m/s² (+2.0 reported), FTTI 1000 ms (ADR-010) |
| Follower check of the braking argument: follower braking, brake lights (ADR-010) | M4 | done: 3.5 m/s² after 1.5 s at 10 m/s³; brake lights with ACC braking (`AOU_ACC_011`, draft) |
| Block condition of checker rule 2: lateral band, `T_ttc`, `T_thw`, `v_close` (ADR-008) | M2 | done: ±2.5 m, 4.0 s, 2.5 s, 0.5 m/s |
| `AccMon` block hold time `T_hold` | M2 | done: 500 ms |
| Plausibility jump limits and speed consistency limit (checker rule 4) | M2 | done: 1 km/h, 3 m, 2 m/s, 0.5 m; 3 km/h over 1 s |
| E2E consecutive-error count `N_e2e` (default 3) | M2 | done: 3 |
| ASIL of `TgtSel` and the decomposition of `AccCtrl` / `AccMon` (ADR-006) | M2 | done: option 2 |
| Tolerance `a_tol` and duration `t_tol` between requested and measured acceleration (detects too little deceleration, ADR-003) | M2 | done: 1.0 m/s², 500 ms |
| TTC threshold `T_tor` for the takeover request at short time-to-collision | M2 | done: 3.0 s |
| TOR display latency (cluster assumption of use) | M2 | done: 200 ms |
| Unintended braking within A-05 is controllable (draft argument in `04`) | M2 | done: confirmed; M4 checks it |

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

M1 closed 2026-10-06: PR #2 merged as `775823e`, tagged `m1`. CI run 37511023867 green on
`1927d40` (the PR page showed `docs-trace-gate` as running after it had finished; a
display issue only).

**Carried into M2 from ADR-003:** an FSR that detects too little deceleration (requested
against measured acceleration); an argument that unintended braking within A-05 is
controllable; the cluster raising the TOR on an ACC message timeout as an `AOU_`.

## 9. M2 plan

Brief §12 M2, refined by ADR-000 D-06, D-10, D-13, D-15, D-16, D-17, D-19 and ADR-003.
Branch `m2-requirements`. Items marked **(pb)** are pb's alone.

**Tooling**
- [x] PLAN.md: close M1, M2 plan (first commit on the branch)
- [x] Graphviz in the image; sphinx-needs `needflow` rendered with Graphviz
- [x] `tools/ears_lint.py` + tests, in `docs-trace-gate`: one EARS template and exactly
      one "shall"; no vague words; a number with a unit where a value is stated; required
      attributes per type; ID prefix matches the directive (M0 note); fails on any
      `⟨pb: …⟩`
- [x] `tools/trace_check.py` v1 + tests, in `docs-trace-gate`: every `SG_` has an `FSR_`,
      every `FSR_` a `TSR_`, every `TSR_` an allocation; no dangling links. Test-related
      rules and `draft` at ASIL ≥ A are warnings until M6
- [x] **ADR-005** (proposed) EARS lint and trace gate v1 rules; also ASIL inheritance
      and the allowed link types

**Requirements**
- [x] `03_stakeholder_and_system_requirements.rst`: `STK_` needs; `SYS_` in EARS for modes
      and transitions (D-11, D-13), HMI, speed and gap control, override, TOR, limits.
      Drafted (7 `STK_`, 37 `SYS_`, all QM per ADR-005); **pb reviews**
- [x] `07_architecture.rst`: minimal `ARC_` elements (`Hmi`, `TgtSel`, `AccCtrl`, `AccMon`,
      RTE, COM, E2E, CanIf, scheduler) as allocation targets; M3 adds the SysML model
- [x] `04_functional_safety_concept.rst`: `FSR_` per safety goal with ASIL, safe state and
      timing within the FTTI; `AOU_` for TOR display, cluster TOR on timeout, actuator
      execution, brake-signal integrity, radar plausibility, radar moving objects only,
      receiver-side E2E check of `ACC_Cmd`; `needflow` per safety goal. Drafted (17 `FSR_`,
      9 `AOU_`) with the draft argument for unintended braking within A-05; **pb reviews**
- [x] `05_technical_safety_concept.rst`: `TSR_` allocated to `ARC_` elements or covered by
      `AOU_`; detection and reaction time budget against each FTTI; `needflow` from each
      safety goal down to the TSRs. Drafted (24 `TSR_`); **pb reviews**
- [x] **ADR-006** (proposed) ASIL decomposition of `AccCtrl` / `AccMon` and the ASIL of
      `TgtSel`, with the independence argument and its limitations (one ECU, shared radar
      input)
- [x] **ADR-007** (proposed) COM and CanIf as QM under the black-channel argument (D-19);
      COM packing sits inside the E2E boundary, so read-back checks are proposed
- [x] **ADR-008** (proposed) block condition of checker rule 2: TTC alone detects the
      scenario-14 fault in steady following too late; TTC or short headway while closing
- [x] **(pb)** accept or change ADR-005 to ADR-008: all four accepted as proposed

**pb**
- [x] **(pb)** values in §5 marked M2 (proposed with reasoning, written in by pb)
- [x] Consistency review of the §5 values: the time budget holds (largest total 760 ms
      against 1000 ms). The jump and consistency limits of `FSR_ACC_010` could fail on
      correct signals with the old `AOU_ACC_007`, and no radar accuracy was assumed. Fixed
      without changing pb's values: `AOU_ACC_007` bounds how fast the ego-speed error
      changes and excludes the road grade from ego acceleration; new `AOU_ACC_010` states
      the radar accuracy (design values, margins worked in the AOUs). Checked and dropped:
      at the 2.0 s gap the block still detects scenario 14 after 0.6 s down to 25 km/h,
      because the fault's own acceleration shortens the headway
- [x] **(pb)** set `status: approved` on all requirements with ASIL ≥ A

**Done when:** EARS lint passes on all requirements; no dangling links; `needflow` diagrams
render from each safety goal down to the TSRs; the decomposition ADR records the
independence argument and its limitations; CI green; pb merges and tags `m2`.

M2 closed 2026-10-13: PR #3 merged as `3ad002a`, tagged `m2`. CI run 38440922615 on `main`
green. All 48 requirements at ASIL ≥ A approved; the 37 `SYS_` are QM and stay `draft`
until pb reviews them.

## 10. M3 plan

Brief §12 M3, refined by ADR-000 D-11, D-14 and ADR-001. Branch `m3-sysml`. Items marked
**(pb)** are pb's alone. M3 sets no safety values.

**Model** (`model/sysml/`, loaded in this order)
- [x] PLAN.md: close M2, M3 plan (first commit on the branch)
- [x] `Interfaces.sysml`: one `item def` per CAN message with its signals and units
      (brief §5.6), E2E fields in a common base; port defs for the messages and for the
      data the components exchange through the RTE
- [x] `AccModes.sysml`: `state def` of the six modes; the D-11 priority order written as
      mutually exclusive guards, one named guard per priority level (`SYS_ACC_001`)
- [x] `SafeCruise.sysml`: item context (radar, vehicle, HMI panel, cluster, actuators, ACC
      ECU) and the ECU structure: one `part def` per `ARC_` element, with the `ARC_` ID as
      its short name; item flows between the components
- [x] `Requirements.sysml`: one requirement usage per allocated `SYS_` / `TSR_`, identified
      by its ID only; text, ASIL and status stay in the requirements database
- [x] `Allocation.sysml`: `satisfy` relations mirroring `allocated_to` in the database;
      the mode machine and the cycle allocated to `AccCtrl` and the scheduler with
      `allocate` (inside the part defs they push the structure views past the renderer's
      element limit)

**Tooling**
- [x] `tools/sysml_check.py` + tests: all model files parse in one kernel session; every
      ID in the model exists in `needs.json` with the matching type; `ARC_` needs and
      `ARC_` part defs match one to one, by ID and name; for every `SYS_` / `TSR_` / `SWR_`
      the set of satisfying parts equals its `allocated_to` set
- [x] Views rendered from the model into `build/` (not committed): item context, ECU
      structure, mode state machine; shown in `07_architecture.rst`
- [x] CI (`docs-trace-gate`): needs export → model check with views → HTML build. The
      broken-ID fixture runs under pytest (`tests/tools/test_sysml_check.py`); the ADR-001
      spike checks moved there too
- [x] **ADR-009** (proposed) SysML model conventions and the consistency check. Includes a
      finding: with the D-14 order, leaving FAULT took two CANCEL presses; proposed fix in
      the model (`AccCtrl` follows the monitor's release)

**pb**
- [x] **(pb)** accept or change ADR-009: accepted as proposed (2026-10-14), including the
      FAULT exit and the allocation rule in both directions
- [x] **(pb)** push a commit with a deliberately broken ID, confirm CI fails, then revert
      (brief *Done when*). `41de707` changes `TSR_ACC_003` to `TSR_ACC_903` in the model.
      On `m3-sysml` its run 38448541179 was cancelled by the revert pushed 11 s later
      (`cancel-in-progress`), so the same commit was pushed to `m3-broken-id-demo`: run
      38533079658 failed in `docs-trace-gate` at "SysML model check and views (ADR-009)",
      all other jobs passed. Revert `404a18e`: run 38448566028 green

**Done when:** the model parses (ADR-001); rendered views (structure, state machine)
appear in `07_architecture.rst`; the consistency check runs in CI and failed once on a
deliberately broken ID, then passed after the revert; CI green; pb merges and tags `m3`.

M3 closed 2026-10-19: PR #4 merged as `189a4b0`, tagged `m3`. CI run 39237853270 on `main`
green.

## 11. M4 plan

Brief §12 M4, refined by ADR-000 D-03, D-11 to D-16, D-22 and ADR-010. Branch `m4-mil`.
Items marked **(pb)** are pb's alone.

**Before the run**
- [x] PLAN.md: close M3, M4 plan (first commit on the branch)
- [x] **ADR-010** (accepted by pb before any MIL code): set-up, hazard criterion and
      assumed FTTI of Experiment A (FTTI of `SG_ACC_001`); set-up and pass criterion of
      Experiment B (follower check of the braking argument in `04`); new `AOU_ACC_011`
      (brake lights with ACC braking, draft)

**Simulation** (`sim/`, Python, deterministic, 10 ms lockstep)
- [ ] Plant: longitudinal ego dynamics, A-10 actuator response, driving resistances,
      receiver check of `ACC_Cmd` and request active flag (`AOU_ACC_004`, `AOU_ACC_005`),
      brake lights (`AOU_ACC_011`)
- [ ] Traffic: scripted lead profiles, cut-in, cut-out, follower (Experiment B)
- [ ] Sensors: radar model (50 ms, 150 m, 4 objects, moving objects only, noise within
      `AOU_ACC_010`, dropouts); `VEH_Dyn` within `AOU_ACC_007`; `HMI_Btn` at 20 ms
- [ ] Message layer: alive counter, E2E check result, error count and message age per
      message, as the RTE inputs of D-14; fault injector (CRC, frozen and skipped counter,
      drop, stuck value, out of range, NaN, forced controller output)
- [ ] ADR-011 MIL harness and model decisions (E2E modelled at the check-result level
      until the DBC exists in M5, radar noise model, time base)

**Reference controller** (`sim/mil_controller/`, float32, D-14 order)
- [ ] `Hmi`, `TgtSel`, `AccCtrl` (mode table of `AccModes.sysml`, ADR-009 FAULT exit,
      control law of brief §5.3), `AccMon` (`TSR_ACC_002` to `TSR_ACC_019`)
- [ ] Per-tick record of the full RTE input vector and the outputs (D-22, for M6)

**Scenarios and tests**
- [ ] 14 scenarios in `sim/scenarios/` (YAML) plus variants (each time gap; CRC, frozen
      and skipped counter; scenario-14 dropout), pass criteria naming requirement IDs;
      runner, KPIs (brief §7.3), plots into the docs build
- [ ] `08_verification_plan.rst`: one `TC_` per scenario, `level: mil`, verifying its
      `SYS_` / `FSR_` / `TSR_` / `AOU_`
- [ ] pytest in `tests/mil/` with `@pytest.mark.tc`; `mil` CI job runs it and hands plots
      and results to `docs-trace-gate`
- [ ] **ADR-012** gain tuning: gains, tuning scenarios, confirmation of the ±10 % of
      `SYS_ACC_028`

**Experiments** (ADR-010)
- [ ] Experiment A and scenario 14 against the FTTI; Experiment B; results from the
      generated artefacts into ADR-010; `SG_ACC_001` changed only by a new ADR

**pb**
- [ ] **(pb)** approve `AOU_ACC_011` (ASIL C)
- [ ] **(pb)** accept or change ADR-011 and ADR-012

**Done when:** all 14 scenarios run in MIL; each has pass/fail against its traced
criteria; plots are generated into the docs build; the FTTI ADR shows assumed vs measured;
safety goals are updated if needed (with ADR); CI green; pb merges and tags `m4`.
