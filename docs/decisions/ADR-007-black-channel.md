# ADR-007 — COM and CanIf as QM under a black-channel argument

- **Status:** accepted
- **Date:** 2026-10-06 (proposed and accepted)
- **Decided by:** pb
- **Relates to:** [ADR-000](ADR-000-project-setup.md) D-14, D-15, D-19;
  [ADR-006](ADR-006-asil-decomposition.md); docs `05_technical_safety_concept`

## Context

D-19 classifies the generated COM code and CanIf as QM under a black-channel argument:
end-to-end protection above COM detects what COM and CanIf could do wrong. The argument
needs a closer look at where E2E sits in the data path.

E2E computes and checks the CRC over the **packed payload bytes**. COM converts between
those bytes and the float32 signal values the components use (D-12). So:

- on **transmit**, the monitor's values pass through COM packing *before* the CRC is
  computed. A packing error is protected by a valid CRC and reaches the actuators;
- on **receive**, the CRC is checked on the bytes, and COM unpacking happens *after* the
  check. An unpacking error reaches the monitor unseen.

Only CanIf and the bus lie between the CRC computation and its check. Without a further
measure, COM is in the safety path at ASIL C (`ACC_Cmd`) and B (inputs).

The faults a black channel must cover (corruption, repetition, loss, delay, insertion,
masquerading, wrong order) are detected for CanIf and the bus by the CRC with data ID,
the alive counter and the timeout (D-15, A-11).

## Options

1. **COM at ASIL C.** Generated code in the safety path with full measures; MISRA
   findings in generated code under a deviation record, plus a tool-confidence argument
   for cantools. Simple, but contradicts D-19.
2. **E2E on signal values.** Compute the CRC over a hand-written canonical encoding of the
   signal values instead of the packed bytes. Bypasses COM, but the receiver needs the
   same encoding, so it duplicates the packing.
3. **QM COM with read-back checks in the E2E component.** On transmit, the E2E component
   unpacks the packed payload and compares it with the values the monitor wrote before it
   protects the payload (`TSR_ACC_023`). On receive, it packs the unpacked signals back
   and compares them with the checked payload (`TSR_ACC_024`). COM stays QM; the checks
   are hand-written at ASIL C / B.

## Proposal

Option 3. It keeps the generated code QM as D-19 intends, and the checks are small and
testable. What it does not catch: a COM error that is consistent in both directions, such
as a wrong scaling in the DBC that pack and unpack share. That is a specification error
of the CAN database, covered by the M5 known-answer tests of the DBC signals and by the
SIL-vECU scenarios, not by the black channel.

**Decision (pb, 2026-10-06):** option 3 as proposed.

## Consequences

- CanIf and the simulated bus are QM black channel. COM is QM with the read-back checks
  of option 3.
- The RTE is not part of the black channel: it carries the monitor's outputs before E2E
  protection (`TSR_ACC_022`, ASIL C). Generated RTE code is covered by the D-14 test
  that the generated scheduler and data flow match the configuration, and by a deviation
  record for MISRA findings (D-19). This is a weaker argument than for hand-written code
  and is listed in the safety case.
- The residual error probability of CRC-8 for a corrupted frame is accepted without a
  number; the project computes no hardware metrics.
