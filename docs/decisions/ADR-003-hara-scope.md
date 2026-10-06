# ADR-003 — HARA scope: operational situations, malfunctions, pruning

- **Status:** accepted
- **Date:** 2026-10-06 (proposed and accepted)
- **Decided by:** pb
- **Relates to:** brief §12 M1, [ADR-000](ADR-000-project-setup.md) D-04, D-05, D-17;
  [ADR-004](ADR-004-hara-representation.md); docs `00_item_definition`, `01_hara`

## Context

ADR-000 D-05 fixes the HARA scope at 5 operational situations × 4 malfunctioning
behaviours, with non-meaningful cells pruned and a one-line reason each. Wet or
low-friction road is a factor within the ratings, not a separate situation. This ADR
records which cells are analysed and which are pruned, and lists scope questions found
while drafting the templates. Full descriptions of the situations and malfunctions are in
`01_hara` (sections *Operational situations* and *Malfunctioning behaviours*).

| ID | Operational situation |
|---|---|
| OS1 | Free motorway driving at high speed, no relevant vehicle ahead |
| OS2 | Steady following in moderate or dense traffic |
| OS3 | Approaching a slower vehicle or the tail of a traffic jam |
| OS4 | Close cut-in ahead of the ego vehicle |
| OS5 | Low-speed boundary near 25 km/h in slowing traffic |

| ID | Malfunctioning behaviour (item level) |
|---|---|
| M1 | Unintended or excessive acceleration |
| M2 | Unintended or excessive deceleration |
| M3 | Insufficient or no deceleration, or loss of control, without a takeover request (as decided below; originally "loss of longitudinal control without a takeover request") |
| M4 | Failure to hand back control on brake pedal or CANCEL |

## Options

1. **Analyse all 20 cells.** No pruning argument needed; some cells repeat others.
2. **Prune cells where the malfunction cannot lead to harm in that situation** (proposed
   below), with a one-line reason each.
3. **Option 2 plus a fifth malfunction** for insufficient deceleration (see open point 1).
   Changes D-05 and needs pb's agreement.

## Proposal

Option 2 with one pruned cell:

| Cell | Proposal | Reason |
|---|---|---|
| OS1 × M3 | prune | With no vehicle ahead, no deceleration is needed, and losing control without a TOR makes the ego vehicle coast; harm needs a vehicle to appear ahead, which is OS3 × M3. |

All other 19 cells are analysed as hazardous events `HE_OS<n>_M<n>`.

Cells kept although they are close to another one (pb may merge them):

- **OS3 × M2 vs OS2 × M2.** Both end in a possible rear-end collision by following
  traffic. Kept apart because in OS3 the driver and following traffic already expect the
  ego vehicle to slow down, which may change controllability and severity.
- **OS1 × M4.** The driver brakes in free driving mostly for something the ACC does not
  see (a stationary object, a hazard outside the radar view). Kept because exactly that
  case is a known limitation of the item.

## Open points

These came up while drafting. Each is decided below.

1. **Insufficient deceleration is not covered.** M1 covers acceleration that is too high,
   M3 covers no control at all. A request that brakes, but less than needed (for example
   −1 m/s² where −3 m/s² is needed while approaching a slower vehicle), falls between
   them. Either define M1 as "acceleration higher than demanded, including too little
   deceleration", or add an M5 (option 3).
2. **Unintended activation.** The ACC starting to control without SET or RESUME is not a
   separate malfunction. Its effects appear as M1 or M2. pb to confirm that this is
   enough, or add it.
3. **Malfunction magnitude.** The authority limits A-04 and A-05 are enforced by the item
   itself (by `AccMon`), so a HARA done without safety mechanisms should not assume them.
   The ratings need a stated assumption: up to what acceleration and deceleration can the
   powertrain and brake system execute an ACC request? If the actuators limit ACC
   requests on their own, that is an assumption of use on them.
4. **Wrong mode display.** The cluster showing ACC as active when it is not is the
   driver-visible part of M3. pb to confirm that M3 covers it.
5. **Hazards from performance limits** (radar misses a target, ACC saturates at A-05 with
   a vehicle braking harder) are ISO 21448 topics and stay outside this HARA. The item
   definition lists them as known limitations.

## Decision

Option 2 as proposed: OS1 × M3 is pruned, the other 19 cells are hazardous events. The
open points are decided as follows.

1. **Insufficient deceleration: M3 is widened** to "insufficient or no deceleration, or
   loss of control, without a takeover request". No M5 is added and M1 is not changed.
   The harm works as in M3 (the driver relies on braking the ACC does not deliver), and the
   worst case of too little deceleration is no deceleration, which M3 already rates. D-05
   keeps four malfunctions.
2. **Unintended activation** is not a separate malfunction. M1 and M2 include acceleration
   or deceleration after an unintended activation; the HARA rates effects, not causes.
3. **Malfunction magnitude:** a malfunctioning request is executed up to the physical
   capability of the actuators, about +3 m/s² and about −8 m/s². No limit on the actuator
   side is credited: the actuators are outside the item and no such limit is specified or
   verified. The values are project assumptions.
4. **Wrong mode display** is covered by the widened M3.
5. **Performance limits** stay outside this HARA (ISO 21448), as known limitations in the
   item definition.

## Consequences

- `01_hara` holds one `HE_` need per analysed cell; the coverage matrix there shows which
  cells are pruned and points here.
- Any later change to situations, malfunctions or pruning needs a new ADR that
  references this one.
- The M3 events and `SG_ACC_003` cover too little deceleration as well as lost control.
  The functional safety concept (M2) needs a way to detect it, for example comparing the
  requested with the measured acceleration (`VEH_Dyn` carries ego acceleration).
- Crediting no actuator limit makes unintended braking (M2) severe; braking that stays
  within A-05 is not visible to a limit check, so the functional safety concept must argue
  that this remainder is controllable.
