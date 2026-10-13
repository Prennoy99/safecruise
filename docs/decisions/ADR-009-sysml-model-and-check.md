# ADR-009 — SysML v2 model conventions and the model check

- **Status:** proposed
- **Date:** 2026-10-13 (proposed)
- **Decided by:** pb (pending)
- **Relates to:** brief §5, §6.3, §12 M3; [ADR-000](ADR-000-project-setup.md) D-11, D-14, D-19;
  [ADR-001](ADR-001-sysml-v2-parsing-in-ci.md); [ADR-005](ADR-005-ears-lint-and-trace-gate.md);
  docs `07_architecture`

## Context

M3 adds a SysML v2 model of the architecture: the item context, the ACC ECU structure,
interfaces mirroring the CAN messages, the mode state machine and the allocation of
requirements to parts. A tool must confirm that the model parses, that every requirement ID
it uses exists in `needs.json`, and that every allocated requirement appears in the model.
The CI check must fail on a broken ID.

The model and the requirements database both hold the architecture elements and the
allocation, so the two can drift. The conventions below decide what lives where, and what
the check can therefore compare mechanically.

Facts about the Pilot kernel 0.62.0, checked for this ADR (2026-10-13):

- `%export <package>` returns the parsed abstract syntax tree as JSON, headlessly. A
  `satisfy` resolves to the requirement element (with its short name) and to the
  satisfying part (with its part definition).
- `%viz` returns SVG headlessly. The renderer stops after 1000 visited model elements,
  marks the view "EXCEEDS THE LIMIT … may be incomplete", and offers no option to raise
  the limit.
- Exporting the five model packages takes about 60 s; parsing and rendering about 25 s.

## Options

**Requirement text in the model**

1. Copy each requirement's text into a `requirement def` with a `doc` comment. Readable
   in the model alone, but there are two copies of every requirement.
2. Generate the requirement elements from `needs.json` before parsing. One source, but
   the model in the repository is incomplete without a generation step.
3. **Stubs by ID.** One requirement usage per allocated requirement, with the ID as its
   short name and a name for readability. The text stays only in the database.

**How the check reads the model**

1. Regular expressions over the source text. Fast; misreads comments and anything the
   expressions do not anticipate.
2. **The parsed model**, through `%export`. Slower; reads what the kernel resolved,
   including which part a `satisfy` names and how that part is typed.

**Strength of the allocation rule.** The brief asks that every requirement with an
allocation exists in the model. Option 1 is that rule only. **Option 2** additionally
requires that the parts satisfying a requirement in the model are exactly its
`allocated_to` elements, in both directions.

## Proposal

1. **Requirements are ID stubs** (`Requirements.sysml`): one requirement usage per
   allocated `SYS_` and `TSR_` (later `SWR_`), e.g. `requirement <'SYS_ACC_001'>
   transitionPriority;`. `FSR_` allocations are not mirrored: the TSRs refine them, and the
   brief limits the allocation to `SYS_` / `TSR_`.
2. **One part def per `ARC_` need**, with the need's ID as short name and its title as
   name (`part def <'ARC_ACC_MON'> AccMon`). Elements outside the ECU (radar, vehicle,
   HMI panel, cluster, actuators) are part defs without an ID, as they are not `ARC_`
   needs.
3. **The database is the source of the allocation.** `Allocation.sysml` holds one
   `satisfy '<ID>' by <part>` per `allocated_to` entry, and a change to an allocation
   changes both in one commit.
4. **`tools/sysml_check.py`** loads the five files in dependency order in one kernel
   session (ADR-001), exports every package and reads the parsed model. Errors:
   - a file does not parse, or a name does not resolve;
   - a short-name ID that does not exist in `needs.json`, or names a need of the wrong
     type (a requirement usage must name a requirement, a part def an `ARC_`);
   - any ID written in the model text, comments included, that does not exist;
   - the same ID used as short name of more than one element;
   - `ARC_` needs and part defs that do not match one to one, by ID and name;
   - a `satisfy` naming a requirement without an ID or a part without an `ARC_` ID;
   - allocation option 2: for every `SYS_`, `TSR_` and `SWR_`, the satisfying parts
     equal its `allocated_to` set, in both directions.
5. **The mode state machine encodes the priority order in its guards.** SysML v2 does not
   rank transitions whose guards hold at the same time. Each priority level of
   `SYS_ACC_001` (D-11) is one named guard that is false while a higher level holds, so
   the guards leaving each state are mutually exclusive. Activation from STANDBY ranks
   below level 3; `SYS_ACC_001` does not list it, and it can only conflict with levels
   1 to 3. The return from OVERRIDE to the mode it left (`SYS_ACC_010`) uses a stored
   `leftMode`. The model describes the machine; the MIL reference (M4) executes it.
6. **Behaviour is allocated with `allocate`**, not with `exhibit` / `perform` inside the
   part defs. Inside the part defs, the structure views visit the 24 transitions and the
   guards and exceed the renderer's limit. `Allocation.sysml` allocates a usage of
   `AccModes` to `accCtrl` and of `EcuCycle` to `sched`.
7. **Views are generated, not committed.** `sysml_check.py --views DIR` renders the item
   context, the ECU structure, the cycle and the state machine into `build/sysml/views/`;
   a view marked as exceeding the limit is an error. The docs job runs: needs export →
   model check with views → HTML build. The needs builder ignores missing images (a hook
   in `docs/conf.py`); the HTML build still fails on a missing view.
8. **Interfaces carry the design names.** One `item def` per CAN message, one attribute
   per signal, ISQ units; port defs per message (the sender owns the def, receivers use
   the conjugate) and for the data exchanged through the RTE. The DBC and
   `rte/swc_config.yaml` in M5 follow these names. Whether the check then compares DBC
   signals and RTE ports with the model is decided in M5.
9. The ADR-001 spike checks (toy model, two broken fixtures) leave the CI docs job; they
   keep running under pytest in `build-unit`.

### Finding: leaving FAULT needs one CANCEL press, not two

Writing the ECU flows showed a conflict between `SYS_ACC_017`, `TSR_ACC_016` and the
runnable order of D-14. `AccMon` releases its latch in the cycle in which it reads CANCEL
and no fault condition holds. `AccCtrl` runs before `AccMon` and reads the latched fault
of the previous cycle. With the guard "CANCEL and no fault", `AccCtrl` sees the CANCEL
while the fault is still reported, then sees no fault one cycle later, when the debounced
CANCEL event is gone. The driver would have to press CANCEL twice.

**Proposed:** `AccCtrl` leaves FAULT when the monitor no longer reports a fault
(`faultReleased = mainSwitchOn and not monitorFault`). The monitor releases only on CANCEL
with no fault condition, so `SYS_ACC_017` holds, 10 ms later, within its 100 ms. The
alternatives are for `AccCtrl` to remember a CANCEL seen in FAULT, or for `Hmi` to hold
the CANCEL event for one more cycle; both add state for the same effect. The requirement
text stays as it is. M4 tests the case in MIL.

## Consequences

- A docs-job run takes about 90 s longer, mostly for `%export`. Local runs of the check
  take as long.
- The rule is stronger than the brief's: a requirement allocated to an element in the
  database but not satisfied by it in the model fails, and so does the reverse.
- The model holds no requirement text, so it is read together with the database. The
  check catches a wrong or stale ID but not a stub name that no longer fits its title.
- Guard exclusivity is shown by review, not checked by a tool. The MIL tests of M4 can
  check it exhaustively over the guard inputs.
- Two flows run against the execution order and are read one cycle later: the mode from
  `AccCtrl` to `Hmi`, and the latched fault from `AccMon` to `AccCtrl`. The second delays
  `AccCtrl`'s FAULT mode by 10 ms; the mode sent in `ACC_Status` does not depend on it,
  because `AccMon` writes FAULT itself (`TSR_ACC_019`).
- A new kernel version may change the export format or the view limit. A kernel upgrade
  already re-runs the ADR-001 fixtures and now also `tests/tools/test_sysml_check.py`.
- SWC-internal elements (M5) that receive `SWR_` allocations need `ARC_` needs and part
  defs of their own, or `SWR_` allocate to the existing components.
