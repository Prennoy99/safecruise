# ADR-000 — Project setup decisions (pre-M0 review)

- **Status:** accepted
- **Date:** 2026-09-30
- **Decided by:** pb
- **Context source:** structured review of the project brief (not published) before M0.

## Context

The brief (§11) lists open decisions to settle before M0, and a review surfaced further
ambiguities that would otherwise bite later (mostly in the back-to-back test and the
safety argument). This ADR records all of them in one place. Each later change to any
item below needs its own ADR that references this one.

No safety ratings, ASILs, FTTIs or safety thresholds are decided here. Those stay with pb
in M1/M2/M4 (see D-17).

---

## Scope

### D-01 Time budget
**Decision:** plan 20–25 working days for M0–M7. M8 and stretch items start only after M7.
Early showable cut-off: M0–M4 plus SIL-lib.
**Rationale:** several items are unproven integrations (SysML v2 pilot in CI,
sphinx-needs + test reports, RTE generator, lockstep vECU over vcan, float32 B2B).

### D-02 Trim order
**Decision:** all four skill profiles (functional safety, systems/MBSE, embedded, test)
stay in. If behind schedule, cut depth in this order: SIL-vECU scope → SysML CI parsing →
RTE generator → MC/DC → safety-case breadth. Protected core: HARA, EARS + trace gate,
doer/checker with scenario 14, MIL + SIL-lib with B2B, unit tests and coverage on
`AccMon`/E2E.
**Rationale:** deciding trims now avoids choosing under time pressure; every profile
keeps at least one strong piece of evidence.

## Open decisions from brief §11

### D-03 MIL language (§11.1)
**Decision:** Python. Optional stretch: rebuild the control law in Simulink and B2B it
against Python, only if a licence is available.
**Rationale:** CI reproducibility without a licence server; easier float32 control.

### D-04 Item boundary (§11.2)
**Decision:** as brief §4.1. Add explicit `AOU_`s for: TOR display latency and visibility
(cluster), actuator execution of the request within A-10, brake-pedal signal integrity,
radar object plausibility. The item definition states that controllability arguments
depend on these.

### D-05 HARA scope (§11.3)
**Decision:** 5 operational situations × 4 malfunctioning behaviours; non-meaningful cells
pruned with a one-line reason each. Wet/low-friction road is a factor within ratings, not
a separate situation. Details recorded in ADR-003.
- Situations: free motorway driving at high speed; steady following in moderate/dense
  traffic; approaching a slower vehicle or traffic-jam tail; close cut-in; low-speed
  boundary near 25 km/h.
- Malfunctions: M1 unintended/excessive acceleration; M2 unintended/excessive
  deceleration; M3 loss of function without TOR; M4 failure to hand back control on
  brake/cancel.

### D-06 `TgtSel` and the checker (§11.4)
**Decision:** `AccMon` runs its own conservative check on the **raw radar object list**
(any valid object within a wide lateral band and below the TTC threshold blocks positive
acceleration). `TgtSel` is on the doer side of the decomposition. Its ASIL is decided by pb
in M2.
**Rationale:** removes `TgtSel` as a common point of failure between doer and checker.
**Consequence:** adjacent-lane objects can block acceleration unnecessarily; documented as
an availability limitation.

### D-07 HIL-lite hardware (§11.5)
**Decision:** hardware bought near project end. Until then only the `socketcan` and `udp`
CanIf backends, behind an interface that lets `serial` / `stm32_fdcan` slot in without
changes above CanIf. Preferred M8 option: real CAN (Nucleo-G474RE + transceiver + USB-CAN
adapter).

### D-08 Compiler and MC/DC (§11.6)
**Decision:** GCC 14 inside the Docker image (D-20), pinned for local and CI via a CMake
preset. MC/DC reported for `AccMon` and E2E.
**Note:** host GCC is 13.3; nothing needs installing on the host.

### D-09 Repository (§11.7)
**Decision:** name `safecruise`, public on GitHub from M0, docs on GitHub Pages. README
carries an "in progress — design and intent only, no results" banner until M7.

## Architecture

### D-10 Output authority of the checker
**Decision:** `AccMon` is the only SWC that writes `ACC_Cmd`. `AccCtrl` writes a proposed
request. On a violation `AccMon` latches its fault, ignores `AccCtrl`, ramps the request
to 0 at bounded jerk, sets request-active = 0 and TOR = 1, and signals the fault to
`AccCtrl`. The latch clears only when the fault is gone **and** the driver presses CANCEL.
`AccCtrl`'s FAULT state keeps mode display and HMI consistent; safety does not depend on it.
**Rationale:** a checker that asks the faulty doer to reach the safe state does not work
(scenario 14).

### D-11 Mode state machine determinism
**Decision:** transitions are evaluated in fixed priority, first match wins, at most one
transition per tick:
1. main switch off → OFF
2. `AccMon` fault → FAULT (TOR per D-13)
3. brake pressed or CANCEL → STANDBY
4. speed < 25 km/h → STANDBY + TOR
5. accelerator > A-12 → OVERRIDE
6. ACTIVE_SPEED ⇄ ACTIVE_FOLLOW arbitration

Gap-fillers: RESUME without a stored set speed is ignored; SET captures current speed
clamped to 30–150 km/h; releasing OVERRIDE below 25 km/h → STANDBY + TOR; ego speed above
150 km/h while active does not deactivate (ACC decelerates to set speed; only activation is
blocked above 150 km/h).
The same table drives the SysML `state def`, the Python MIL and the C implementation.

### D-12 Numeric types
**Decision:** float32 in the SWCs. CAN signals stay scaled integers; COM converts at the
boundary. `float` literals only, `-Wdouble-promotion -Wfloat-conversion` on,
`-ffast-math` and similar flags forbidden. MIL uses `np.float32` with matching order of
operations where practical. Fixed-point is mentioned in the README, not built.

### D-13 Faults outside active modes and at startup
**Decision:**
- Inputs start as "never received": activation is inhibited, no fault. A timeout fault
  exists only after a message has been received at least once.
- Fault in STANDBY → FAULT **without** TOR ("ACC unavailable", activation blocked).
- Fault in ACTIVE_* or OVERRIDE → FAULT + TOR; `AccMon` ramps its own request to 0.

### D-14 Runnable order and data flow
**Decision:** fixed order per 10 ms tick: COM receive + E2E check → `Hmi` → `TgtSel` →
`AccCtrl` → `AccMon` → COM transmit. RTE ports are static buffers with same-tick
propagation. The order is declared once in `rte/swc_config.yaml`; a test asserts the
generated scheduler and the MIL step function agree. The RTE exposes a new-data flag and
an age counter per message for timeout handling (A-11).

### D-15 E2E protection
**Decision:** E2E-Profile-1-style (named only; no specification text reproduced):
- CRC-8 SAE J1850 (poly 0x1D) over payload, alive counter and a per-message **Data ID**
  that is included in the CRC but not transmitted.
- 4-bit alive counter: increment of exactly 1 is valid; repeat (frozen) or jump > 1
  (skipped) is an E2E error. Lost frames are handled by the A-11 timeout, not by counter
  tolerance.
- A single bad frame is discarded (last valid value held, but ageing). N consecutive
  E2E errors on one message → fault (N = 3 by default; value confirmed by pb in M2).
- `ACC_Cmd` is also protected; the receiver-side check is an `AOU_` and is implemented in
  the sim plant.

### D-16 `AccMon` raw-object check: dropouts and stationary objects
**Decision:**
- Once the block condition is met, it holds for at least `T_hold` after the condition was
  last true. Value set by pb (placeholder `⟨pb: T_hold⟩`).
- The radar model reports moving objects only, recorded as an `AOU_` on the radar
  (consistent with non-goal §2.5).
- Scenario 14 gets a variant with a 1–2 radar-frame dropout of the close target while the
  doer is forced to +2 m/s²; the block must hold.

## Requirements and data

### D-17 Authorship and approval
**Decision:** pb authors ASILs, safe states, FTTIs, the FTTI hazard criterion and every
safety threshold (TTC threshold, plausibility jump limits, E2E error count, `T_hold`).
Requirement wording, derivation links and allocations are drafted with visible
`⟨pb: …⟩` placeholders; the EARS linter fails on remaining placeholders. Requirements
carry `status: draft | approved`; only pb sets `approved`. The trace gate warns on
`draft` during a milestone; a milestone is done only with zero `draft` requirements at
ASIL ≥ A.

### D-18 Test-to-requirement linkage
**Decision:** pytest uses a marker `@pytest.mark.tc("TC_…")`; a `conftest.py` hook writes the
IDs as JUnit `<property name="tc">`. Unity tests use the naming convention
`test_TC_…`. Scenario YAML pass criteria list the requirement IDs they verify, and
`trace_check.py` confirms they exist. Each `TC_` declares its `level` list; the gate
requires a pass at every declared level.

### D-19 Generated code and MISRA
**Decision:** cantools COM code and the RTE are generated into `build/`, not committed;
generator versions pinned. COM and CanIf are QM under a **black-channel** argument (E2E
above COM detects corruption), recorded in the TSC and an ADR. Generated code is scanned
and reported, covered by one deviation record per generator. Hand-written `bsw/e2e/` and
the RTE generator templates: full MISRA, zero undocumented findings.

## CI and deployment

### D-20 Toolchain
**Decision:** one pinned Docker image (`Dockerfile` + `.devcontainer/`) for local work and
CI: GCC 14, CMake, cppcheck + MISRA addon, lizard, gcovr, Python 3.12 with locked
dependencies, Java + SysML v2 Pilot Implementation, later `arm-none-eabi-gcc`. The
SIL-vECU job loads `vcan` on the runner host and runs the container with `--network=host`
(verified in Spike 2, ADR-002).

### D-21 Git workflow and gating
**Decision:** protected `main`; one branch and PR per milestone with the *Done when*
evidence in the PR description; pb merges; tags `m0`, `m1`, …. Required CI jobs:
`build-unit`, `static-analysis`, `mil`, `sil-lib`, `sil-vecu`, `docs-trace-gate`. Pages
deploys from `main` only.

## Test strategy

### D-22 Back-to-back is open loop
**Decision:** MIL runs closed loop and records the full per-tick RTE input vector; SIL-lib
replays exactly that vector. Compared per tick: state (identical) and request (within ε).
Closed-loop SIL-lib and SIL-vECU runs are judged against scenario pass criteria and KPIs,
not against MIL bit-for-bit. Threshold-edge divergences are investigated and explained in
an ADR, never fixed by loosening ε.
**Rationale:** in closed loop, tiny numeric differences move the plant and cause
threshold crossings one tick apart that are not controller bugs.

---

## Consequences

- Brief §5.2 is extended by D-11 and D-13 (priority order, split fault transition).
- Brief §5.4 is sharpened by D-06, D-10 and D-16 (raw-object check, output authority,
  hold time).
- Brief §6.3 test linkage changes from function names to markers for pytest (D-18).
- Brief §7.5 is clarified as open-loop B2B (D-22).
- New `AOU_`s to create in M2: TOR display, actuator execution, brake-signal integrity,
  radar plausibility, radar reports moving objects only, receiver-side E2E check of
  `ACC_Cmd`.
