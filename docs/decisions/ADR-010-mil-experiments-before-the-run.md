# ADR-010 — MIL experiments fixed before the run: FTTI of SG_ACC_001 and the follower check

- **Status:** accepted
- **Date:** 2026-10-19 (proposed and accepted before any MIL code existed)
- **Decided by:** pb
- **Relates to:** brief §7.6, §12 M4; [ADR-000](ADR-000-project-setup.md) D-17;
  [ADR-003](ADR-003-hara-scope.md); [ADR-008](ADR-008-acceleration-block-condition.md);
  docs `02_safety_goals` (`SG_ACC_001`), `04_functional_safety_concept` (argument
  "Unintended acceleration or braking within the limits", `AOU_ACC_011`),
  `05_technical_safety_concept` (time budget)

## Context

Two claims of the concept phase rest on hand calculations that M4 checks in MIL:

1. **FTTI of `SG_ACC_001` (1000 ms).** Its basis in `02`: at 100 km/h and a 1.0 s gap,
   +3 m/s² brings the time headway below 0.5 s after about 3 s.
2. **Unintended braking within A-05 is controllable** for following traffic (`04`): a
   follower at a 1 s gap with 1.5 s reaction time does not collide. The argument does not
   say how hard the follower brakes, and it relies on the brake lights coming on at the
   start of the braking without stating that as an assumption of use.

Brief §7.6 requires the hazard criterion and the assumed FTTI to be fixed before the run,
so that the result cannot shape the criterion. This ADR fixes the set-up and the pass
criteria of both experiments. The commit that adds it comes before any MIL code on the
M4 branch.

## Decision

### Experiment A — FTTI of `SG_ACC_001`

**Set-up**
- Level road, no wind. Lead at a constant 100 km/h.
- Ego in ACTIVE_FOLLOW with the 1.0 s time gap (A-02), settled: equal speeds, distance
  5 m + 1.0 s × v = 32.8 m (spacing policy with A-03).
- Fault: from t₀ the acceleration request that reaches the plant is +3.0 m/s², held. This
  is the malfunction magnitude rated in the HARA (ADR-003: actuator capability, no actuator
  limit credited). The fault is injected at the ECU output with the monitor bypassed, so
  the run measures the time the item has without the safety mechanism.
- Variant: +2.0 m/s² (A-04, the magnitude of scenario 14). Reported; the main case
  decides.

**Hazard criterion:** time headway below **0.5 s**, computed from the true range and true
ego speed of the plant (not from the radar model).

**Measured value:** t_hazard − t₀ in whole 10 ms ticks, where t₀ is the first tick in which
the faulty request is sent and t_hazard the first tick in which the criterion holds.

**Assumed FTTI:** **1000 ms** (`SG_ACC_001`, unchanged).

**Also reported, without pass/fail:** time to TTC < 2 s, time to contact, lowest TTC.

**Evaluation**
- Measured ≥ assumed: the assumed FTTI stands. A large margin does not raise the FTTI;
  that would need its own ADR.
- Measured < assumed: the FTTI of `SG_ACC_001` and the time budget in `05` are revised
  with a new ADR before M4 closes.

**Scenario 14 against this FTTI** (monitor on, controller forced to +2 m/s² toward the
close lead): pass if (a) the time from t₀ to the first `ACC_Cmd` with the request at or
below 0 m/s² and the request active flag cleared, plus 450 ms for the actuator (the
convention of the time budget in `05`), is at most 1000 ms, and (b) the hazard criterion is
not reached anywhere in the run.

**Hand estimate** (for this decision, not a result; A-10 actuator response, no driving
resistances, lead at constant speed):

| Fault | Time headway < 0.5 s | TTC < 2 s | Contact |
|---|---|---|---|
| +3.0 m/s² | 3.51 s | 3.52 s | 5.11 s |
| +2.0 m/s² | 4.31 s | 4.50 s | 6.16 s |

The "about 3 s" in `02` used a start distance of 1.0 s × v without the 5 m offset. The
+2.0 m/s² row agrees with the 4.3 s of ADR-008.

### Experiment B — follower braking check

**Set-up**
- Level road. Ego at 100 km/h in ACTIVE_SPEED, no vehicle ahead.
- Follower behind the ego at 100 km/h and 1.0 s × v = 27.8 m (a driver's time gap, no
  offset).
- Fault: from t₀ the controller's proposed request ramps to −3.5 m/s² at 2.5 m/s³ and
  holds until the end of the run. This is inside the limits of `FSR_ACC_001`, so the
  monitor (on) does not detect it. The ego driver does not intervene.
- Brake lights: on from the first tick in which the plant executes a negative ACC request,
  i.e. after the 50 ms dead time of A-10 (`AOU_ACC_011`).
- Follower: reacts 1.5 s after the brake lights come on; its deceleration then builds at
  10 m/s³ to **3.5 m/s²** and holds to standstill. The follower brakes no harder than the
  faulty ACC does.

**Pass criterion:** the closest bumper-to-bumper distance between follower and ego stays
above 0 m. Reported: closest distance, lowest time headway of the follower.

**Sensitivity** (hand estimate, closest distance in m; ego braking to standstill):

| Brake lights on when | Follower 3.5 m/s² | 4.0 m/s² | 5.0 m/s² | 6.0 m/s² |
|---|---|---|---|---|
| the brakes apply the ACC request (50 ms) | 11.2 | 22.2 | 24.8 | 25.2 |
| ego deceleration > 0.5 m/s² | −2.1 | 11.0 | 19.8 | 21.5 |
| ego deceleration > 1.0 m/s² | −9.2 | 3.9 | 16.0 | 18.6 |

The argument holds with a 3.5 m/s² follower only if the brake lights come on with the
brake request. A vehicle that first decelerates on engine drag without brake lights would
need a follower braking at about 5 m/s². This dependency is why the brake lights become an
assumption of use.

## Options considered

**Hazard criterion**
1. **Time headway < 0.5 s (chosen).** The basis of the approved FTTI of `SG_ACC_001`, so
   the experiment tests the argument that was approved; lowest time headway is already a
   KPI (brief §7.3). Weakness: it ignores closing speed. The experiment starts from steady
   following, so closing speed is zero at t₀; TTC is reported alongside.
2. TTC < 2 s. Similar timing here (3.52 s), but undefined at t₀ (no closing speed).
3. Contact. Too late to be a hazard criterion.

**Fault magnitude:** +3.0 m/s² (chosen, ADR-003 rates the malfunction at actuator
capability, which supersedes the A-04 of brief §7.6) with +2.0 m/s² reported.

**Follower check**
1. **New `AOU_ACC_011` (brake lights with any executed ACC brake request) and a follower
   at 3.5 m/s² (chosen).** Makes the assumption the argument already made explicit.
2. No assumption, follower at 5.0 m/s². Relies on firm braking by the following driver,
   which weakens the controllability claim.
3. Both, with option 2 reported only.

## Consequences

- New `AOU_ACC_011` in `04`, derived from `FSR_ACC_001` (ASIL C), status `draft` until pb
  approves it; the braking argument in `04` refers to it and to Experiment B.
- The results are added to this ADR in a "Results" section after the run, taken only from
  the generated MIL artefacts. `SG_ACC_001` changes only through a new ADR.
- Not covered by an experiment: the 500 ms FTTIs of `SG_ACC_002` and `SG_ACC_004` stay
  argued by the time budget in `05`. Experiment B checks the controllability of the
  remainder of `SG_ACC_002`, not its FTTI.
