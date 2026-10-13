# ADR-008 — Condition of the monitor's acceleration block

- **Status:** accepted
- **Date:** 2026-10-06 (proposed and accepted)
- **Decided by:** pb
- **Relates to:** brief §5.4 (checker rule 2), §7.2 (scenario 14), §7.6;
  [ADR-000](ADR-000-project-setup.md) D-06, D-16, D-17; [ADR-006](ADR-006-asil-decomposition.md);
  docs `02_safety_goals`, `04_functional_safety_concept`

## Context

Checker rule 2 blocks a positive acceleration request while a relevant target has a
time-to-collision (TTC) below a threshold. Scenario 14 forces the controller to +2 m/s²
toward a close target and requires the monitor to reach the safe state within the FTTI of
`SG_ACC_001` (1000 ms).

In steady following the ego and lead speeds are equal, so the TTC is infinite. A forced
acceleration has to build up a closing speed first, and the TTC falls below a 4 s
threshold only seconds after the fault.

**Estimate.** A hand calculation for this decision, not a verification result; M4 repeats
it in MIL. Lead at constant speed, ego at the selected gap (spacing policy with A-02,
A-03), +2 m/s² from t = 0 through the actuator response of A-10. After detection the
request is cut to 0 m/s², and the driver brakes at −6 m/s² 1.5 s after the takeover
request. The hazard criterion used as an example is a time headway below 0.5 s (brief §7.6;
pb sets the real criterion in M4).

| Gap, speed | TTC < 4 s: detected after | Lowest time headway | TTC < 4 s, or time headway < 2.5 s while closing > 0.5 m/s: detected after | Lowest time headway |
|---|---|---|---|---|
| 1.0 s, 100 km/h | 3.4 s | 0.34 s | 0.6 s | 1.07 s |
| 1.0 s, 150 km/h | 4.4 s | 0.28 s | 0.6 s | 1.05 s |
| 1.0 s, 30 km/h | 1.8 s | 0.49 s | 0.6 s | 1.22 s |
| 1.5 s, 100 km/h | 4.4 s | 0.41 s | 0.6 s | 1.55 s |
| 2.0 s, 100 km/h | 5.2 s | 0.46 s | 0.6 s | 2.03 s |

Without a monitor, the time headway falls below 0.5 s after 4.3 s and the vehicles
collide after 6.2 s (1.0 s gap, 100 km/h).

## Options

1. **TTC only** (brief). Simple. Detects the scenario-14 fault 1.8–5.2 s after onset,
   beyond the 1000 ms FTTI, and the estimate reaches the example hazard criterion in most
   cases.
2. **TTC, or short time headway while closing.** Block while TTC < `T_ttc`, **or** time
   headway < `T_thw` while the closing speed exceeds `v_close`. In steady following, a
   wrong acceleration is caught as soon as the closing speed builds up, independent of
   the TTC.
3. **Time headway only.** Misses fast approaches from far away (closing on a much slower
   vehicle at a long headway), which the TTC catches.

## Proposal

Option 2, with these consequences:

- **The controller applies the same rule** (`TSR_ACC_004`). Otherwise the controller
  would accelerate legitimately inside the block, for example to close a large gap, and
  the monitor would raise a fault with a takeover request each time. With the rule on
  both sides, a conflict means a controller fault (`TSR_ACC_005`).
- **Availability.** The ACC cannot close a gap toward a vehicle within `T_thw` faster
  than `v_close`. Closing a too-large gap behind a vehicle at the same speed is slow. This
  adds to the adjacent-lane limitation of D-06 and goes into the known limitations.
- **Radar noise.** `v_close` must stay above the range-rate noise of the radar, or the
  block flickers in steady following. `T_hold` (D-16) covers short dropouts.

**Decision (pb, 2026-10-06):** option 2 with a lateral band of ±2.5 m, `T_ttc` = 4.0 s,
`T_thw` = 2.5 s and `v_close` = 0.5 m/s; `T_hold` = 500 ms (D-16).

## Consequences

- `FSR_ACC_002` and `TSR_ACC_003`/`004` use the condition of option 2.
- Scenario 14 gets variants in steady following at each time gap, besides the
  close-target and dropout variants (D-16).
- The FTTI experiment in M4 measures the detection time of the chosen condition.
