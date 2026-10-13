# ADR-006 — ASIL decomposition of AccCtrl / AccMon and the ASIL of TgtSel

- **Status:** accepted
- **Date:** 2026-10-06 (proposed and accepted)
- **Decided by:** pb
- **Relates to:** brief §1.3, §5.1, §9; [ADR-000](ADR-000-project-setup.md) D-06, D-10, D-16,
  D-17; [ADR-005](ADR-005-ears-lint-and-trace-gate.md); [ADR-008](ADR-008-acceleration-block-condition.md);
  docs `04_functional_safety_concept`, `05_technical_safety_concept`

## Context

The safety goals are ASIL B (`SG_ACC_001`, `003`, `004`) and C (`SG_ACC_002`). The
controller `AccCtrl` (mode logic and control law) is the complex part of the software. The
monitor `AccMon` is small, reads the raw inputs and owns the output command (D-10). The
functional safety concept gives the monitor every mechanism the safety goals need:
limits, the acceleration block, driver precedence, input integrity, the fault latch and
the safe-state reactions. The question is which ASIL each component is developed to, and
whether that can be argued as an ASIL decomposition (ISO 26262-9, clause 5, named only).

## Options

1. **No decomposition.** `AccCtrl` and `AccMon` both at ASIL C. The complex controller
   would carry the full verification load of ASIL C (coverage, MISRA, reviews).
2. **QM(x) controller + x(x) monitor** for the requirements both sides meet: limits
   (`TSR_ACC_001`/`002`), the acceleration block (`003`/`004`), brake pedal and CANCEL
   (`007`/`008`). Monitor-only mechanisms keep their full ASIL. `AccCtrl` is QM, `AccMon`
   is ASIL C.
3. **B(C) controller + A(C) monitor.** Spreads the effort, but the monitor is the element
   that reaches the safe state on its own, so it is the wrong place to lower the ASIL, and
   the controller would need ASIL B verification.

## Proposal

Option 2 (the brief's doer/checker idea):

| Requirement pair | `AccCtrl` (doer) | `AccMon` (checker) |
|---|---|---|
| Limits, `FSR_ACC_001` (C) | `TSR_ACC_001` QM(C) | `TSR_ACC_002` C(C) |
| Acceleration block, `FSR_ACC_002`/`003` (B) | `TSR_ACC_004` QM(B) | `TSR_ACC_003` B(B) |
| Brake pedal and CANCEL, `FSR_ACC_006` (B) | `TSR_ACC_008` QM(B) | `TSR_ACC_007` B(B) |

- **`AccMon`: ASIL C**, the highest ASIL of its requirements.
- **`AccCtrl`: QM.** It carries only QM(x) requirements and nominal `SYS_` requirements.
- **`TgtSel`: QM.** The monitor does not use the selected target (D-06); a wrong selection
  can only make the controller propose a wrong request, which the monitor checks.
- **`Hmi`: QM.** The monitor reads SET, RESUME, CANCEL and the pedals itself
  (`TSR_ACC_006`, `TSR_ACC_007`).
- E2E, RTE and scheduler carry the ASIL of the safety requirements they implement
  (`TSR_ACC_010`, `011`, `020`–`024`; up to C). COM and CanIf: ADR-007.
- The monitor also writes the mode field of `ACC_Status` while a fault is latched
  (`TSR_ACC_019`), so the mode display does not depend on the controller. This extends
  D-10, where the monitor owned `ACC_Cmd` only.

**Decision (pb, 2026-10-06):** option 2 as proposed, with the ASILs in the table above.

## Independence argument

What makes the two sides independent:

- **Separate components with one-way data flow.** The monitor reads one value from the
  controller, the proposed request, and only to check it. It reads the radar object list,
  pedals and buttons from the RTE itself, not from `TgtSel`, `Hmi` or `AccCtrl`.
- **Output authority.** Only the monitor writes `ACC_Cmd`. A faulty controller cannot
  bypass it, and the safe state does not need the controller's help (D-10).
- **Separate requirements.** The monitor's rules come from the FSRs, not from the control
  law. The block rule is the one rule both apply; they implement it separately.
- **Detection outside the ECU.** The alive counter of `ACC_Cmd` advances only when the
  monitor has run (`TSR_ACC_020`), so a stalled monitor or a silent ECU is detected by the
  actuators and the cluster (`AOU_ACC_002`, `AOU_ACC_004`).

## Limitations

These weaken the argument and are stated, not solved:

1. **One ECU, one process.** Doer and checker share the processor, memory and scheduler.
   No memory partitioning (MPU) and no timing supervision (watchdog) exist, so freedom from
   interference is not shown: a controller bug that overwrites monitor data is not
   excluded. M8 may add a hardware watchdog as a first step.
2. **Shared inputs.** Both sides read the same radar data. A radar object that is
   plausible but wrong defeats both; it is covered by `AOU_ACC_008`, not by software.
3. **Shared block rule.** Doer and checker implement the same formula from the same
   requirement. An error in that requirement (a wrong threshold) is a common cause.
4. **No diversity of development.** The same person, toolchain, compiler and coding
   rules build both sides. A real decomposition would also look at dependent failures in
   the development process (ISO 26262-9, clause 7, named only).
5. **Shared generated code.** RTE and COM are generated and used by both sides.

## Consequences

- `AccMon`, the E2E component and the safety paths of the RTE get the ASIL C measures of
  the verification table (brief §8): MISRA with zero undocumented findings, 100 % statement
  and branch coverage, MC/DC reported. `AccCtrl`, `TgtSel` and `Hmi` get the QM measures.
- The trace gate checks that each decomposed ASIL inherits its parent's target ASIL
  (ADR-005).
- The limitations go into the README and the safety case.
