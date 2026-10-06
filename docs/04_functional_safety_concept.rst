Functional safety concept
=========================

:Status: draft. Safety values set by pb on 2026-10-06 (ADR-000 D-17); each requirement
         stays ``draft`` until pb approves it.
:Applies: ISO 26262-3, clause 7 (functional safety concept), as applied concepts only

The functional safety requirements (``FSR_``) say how the item meets each safety goal of
:doc:`02_safety_goals`: which faults are detected, how the item reaches the safe state,
how the driver is warned, and what the item relies on from the elements outside the ACC
ECU (assumptions of use, ``AOU_``). Each ``FSR_`` derives from the safety goals it serves
and inherits the highest of their ASILs (ADR-005). The technical safety concept
(:doc:`05_technical_safety_concept`) allocates them to the architecture and shows the
time budget against each FTTI.

Principles
----------

- **Doer and checker.** ``AccCtrl`` proposes the acceleration request. ``AccMon`` checks it
  against the limits and the situation, owns ``ACC_Cmd``, and forces the safe state
  without help from ``AccCtrl`` (ADR-000 D-10). The decomposition is argued in ADR-006.
- **The checker reads raw inputs.** ``AccMon`` reads the radar object list, the pedals
  and the buttons directly, not through ``TgtSel``, ``Hmi`` or ``AccCtrl`` (ADR-000
  D-06).
- **A fault is latched.** A detected fault holds until it is gone and the driver presses
  CANCEL (ADR-000 D-10).
- **Safe state per goal.** The reaction depends on the sign of the request at the fault:
  a positive request is cut at once (``SG_ACC_001``), a negative one is limited and then
  ramped out (``SG_ACC_002``); the driver gets a takeover request in both cases
  (``SG_ACC_003``).
- **Timing.** Each reaction is bounded by the FTTI of its goal. The split into detection,
  reaction and actuator response is in :doc:`05_technical_safety_concept`.

Fault detection
---------------

.. fsr:: Acceleration and jerk limits
   :id: FSR_ACC_001
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_002
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   If the acceleration request proposed by the controller is outside −3.5 to +2.0 m/s²,
   or changes faster than 2.5 m/s³, then the ACC system shall report a fault.

   A-04, A-05, A-06; checker rule 1. The request that leaves the ECU never exceeds the
   limits, because the monitor sends the limited value (:need:`FSR_ACC_014`,
   :need:`FSR_ACC_015`). This is the mechanism that removes the −8 m/s² malfunction rated
   in the HARA (ADR-003).

.. fsr:: No positive acceleration near a close object
   :id: FSR_ACC_002
   :status: draft
   :derives_from: SG_ACC_001
   :allocated_to: ARC_ACC_MON, ARC_ACC_CTRL
   :asil: B
   :verification_method: test

   While a valid radar object within a lateral offset of ±2.5 m has a
   time-to-collision below 4.0 s, or a time headway below 2.5 s while
   closing faster than 0.5 m/s, the ACC system shall send no positive
   acceleration request.

   Checker rule 2, widened by ADR-008: a time-to-collision rule alone detects an
   unintended acceleration in steady following seconds too late. The monitor applies the
   rule to the raw object list in a band wider than the target selection (ADR-000 D-06);
   the controller applies the same rule, so a healthy controller never conflicts with it
   (:need:`FSR_ACC_004`). Time-to-collision is range divided by closing speed; time
   headway is range divided by ego speed.

.. fsr:: Hold of the acceleration block
   :id: FSR_ACC_003
   :status: draft
   :derives_from: SG_ACC_001
   :allocated_to: ARC_ACC_MON, ARC_ACC_CTRL
   :asil: B
   :verification_method: test

   When the condition of :need:`FSR_ACC_002` ends, the ACC system shall keep sending no
   positive acceleration request for 500 ms.

   ADR-000 D-16: a radar dropout of the close target for 1 or 2 radar frames must not
   release the block. Scenario 14, dropout variant.

.. fsr:: Acceleration against the block is a fault
   :id: FSR_ACC_004
   :status: draft
   :derives_from: SG_ACC_001
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If the controller proposes a positive acceleration request while :need:`FSR_ACC_002`
   or :need:`FSR_ACC_003` blocks positive acceleration, then the ACC system shall report a
   fault.

   Scenario 14: the controller is forced to +2 m/s² toward a close target.

.. fsr:: Request only after driver activation
   :id: FSR_ACC_005
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_002, SG_ACC_004
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   The ACC system shall send an acceleration request only after a press of SET or RESUME
   that came later than the last brake pedal press, CANCEL press, main switch off,
   reported fault and start of the ECU.

   Covers unintended activation, which the HARA rates as part of M1 and M2 (ADR-003),
   and "no request after CANCEL" in the safe state of ``SG_ACC_004``. The accelerator
   override does not end the activation; the brake pedal does.

.. fsr:: Brake pedal and CANCEL end the request
   :id: FSR_ACC_006
   :status: draft
   :derives_from: SG_ACC_004, SG_ACC_001
   :allocated_to: ARC_ACC_MON, ARC_ACC_CTRL
   :asil: B
   :verification_method: test

   When the driver presses the brake pedal or CANCEL, the ACC system shall clear the
   request active flag within 500 ms.

   FTTI of ``SG_ACC_004``; checker rule 5. The monitor acts on the raw pedal and button
   signals, independent of the mode of the controller.

.. fsr:: Accelerator pedal ends ACC braking
   :id: FSR_ACC_007
   :status: draft
   :derives_from: SG_ACC_002
   :allocated_to: ARC_ACC_MON, ARC_ACC_CTRL
   :asil: C
   :verification_method: test

   When the accelerator pedal position exceeds 5 %, the ACC system shall clear the request
   active flag within 500 ms.

   A-12; FTTI of ``SG_ACC_002``. The driver's way out of unintended braking within the
   ACC authority (see `Unintended acceleration or braking within the limits`_).

.. fsr:: Input end-to-end fault
   :id: FSR_ACC_008
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_003, SG_ACC_004
   :allocated_to: ARC_E2E, ARC_ACC_MON
   :asil: B
   :verification_method: test

   If a received ``RDR_Obj1..4``, ``VEH_Dyn`` or ``HMI_Btn`` message fails its end-to-end
   check in 3 consecutive messages, then the ACC system shall report a fault.

   ADR-000 D-15 (default 3). A single bad message is discarded and the last valid value
   is held (:need:`SYS_ACC_036`).

.. fsr:: Input timeout
   :id: FSR_ACC_009
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_003, SG_ACC_004
   :allocated_to: ARC_RTE, ARC_ACC_MON
   :asil: B
   :verification_method: test

   If a message that was received at least once is missing for 3 consecutive cycles of
   that message, then the ACC system shall report a fault.

   A-11; ADR-000 D-13. Same behaviour as :need:`SYS_ACC_037`, here with the integrity of
   the safety goals.

.. fsr:: Input plausibility
   :id: FSR_ACC_010
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_003
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If ego speed, ego acceleration, or the range, range rate or lateral offset of a radar
   object is not a number, outside its signal range, changes between two consecutive
   messages by more than 1 km/h for ego speed, 3 m for range, 2 m/s for range rate or 0.5 m for lateral offset, or ego speed departs from the integral of ego
   acceleration by more than 3 km/h over 1 s, then the ACC system shall
   report a fault.

   Checker rule 4; scenario 13 (stuck or implausible ego speed). Radar jumps are checked
   per object ID; a new ID is a new object, not a jump. Signal ranges come from the CAN
   database (M5).

.. fsr:: Too little deceleration
   :id: FSR_ACC_011
   :status: draft
   :derives_from: SG_ACC_003
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If the measured ego acceleration is above the expected response to a deceleration
   request of the ACC system by more than 1.0 m/s² for longer than
   500 ms, then the ACC system shall report a fault.

   ADR-003: detects deceleration that the actuators do not deliver. The expected response
   is the request passed through the actuator response of A-10.

.. fsr:: Takeover request at short time-to-collision
   :id: FSR_ACC_012
   :status: draft
   :derives_from: SG_ACC_003
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   While the ACC system is active and a valid radar object within a lateral offset of
   ±2.5 m has a time-to-collision below 3.0 s, the ACC system shall
   raise the takeover request.

   Covers a controller that brakes too little for the situation, which
   :need:`FSR_ACC_011` cannot see (the actuators deliver what was requested). Not a fault:
   a healthy controller keeps braking, and the driver is asked to help.

Fault reaction
--------------

.. fsr:: Fault latch
   :id: FSR_ACC_013
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_002, SG_ACC_003, SG_ACC_004
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   When the ACC system reports a fault, the ACC system shall keep the fault until the
   fault condition is gone and the driver presses CANCEL.

   ADR-000 D-10; :need:`SYS_ACC_017`.

.. fsr:: Safe state for a positive request
   :id: FSR_ACC_014
   :status: draft
   :derives_from: SG_ACC_001
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If a fault occurs while the acceleration request is positive, then the ACC system shall
   set the request to 0 m/s² without a jerk limit and clear the request active flag within
   1000 ms.

   Safe state and FTTI of ``SG_ACC_001``.

.. fsr:: Safe state for a negative request
   :id: FSR_ACC_015
   :status: draft
   :derives_from: SG_ACC_002
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   If a fault occurs while the acceleration request is negative, then the ACC system shall
   limit the request to −3.5 m/s² within 500 ms and then ramp it to 0 m/s² at 2.5 m/s³
   before it clears the request active flag.

   Safe state and FTTI of ``SG_ACC_002``. The ramp gives the driver time to take over
   braking that is still needed.

.. fsr:: Takeover request and mode on a fault
   :id: FSR_ACC_016
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_002, SG_ACC_003
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   If a fault occurs while the ACC system is active or in override, then the ACC system
   shall raise the takeover request and report ACC as not active to the cluster within
   1000 ms.

   Safe states of ``SG_ACC_001`` to ``SG_ACC_003``; FTTI of ``SG_ACC_003``, which
   includes the cluster's display latency (:need:`AOU_ACC_001`). A fault in STANDBY gives
   no takeover request (ADR-000 D-13).

.. fsr:: Protected command output
   :id: FSR_ACC_017
   :status: draft
   :derives_from: SG_ACC_001, SG_ACC_002, SG_ACC_003, SG_ACC_004
   :allocated_to: ARC_E2E, ARC_ACC_MON
   :asil: C
   :verification_method: test

   The ACC system shall send ``ACC_Cmd`` and ``ACC_Status`` with a CRC-8 and an alive
   counter that advances only in cycles in which the monitor has run.

   A stalled monitor, a corrupted command or a silent ECU is detected by the receivers
   (:need:`AOU_ACC_002`, :need:`AOU_ACC_004`).

Assumptions of use
------------------

Requirements on elements outside the ACC ECU, which are simulated in this project
(ADR-000 D-04, D-15, D-16; :doc:`00_item_definition`). The simulation implements them;
a real vehicle would have to show them.

.. aou:: TOR display
   :id: AOU_ACC_001
   :status: draft
   :derives_from: FSR_ACC_012, FSR_ACC_016
   :asil: C

   When ``ACC_Cmd`` carries the takeover request, the instrument cluster shall show it
   with a visual and an acoustic signal within 200 ms.

.. aou:: Cluster on loss of the ACC messages
   :id: AOU_ACC_002
   :status: draft
   :derives_from: FSR_ACC_016, FSR_ACC_017
   :asil: C

   If ``ACC_Cmd`` or ``ACC_Status`` is missing or fails its end-to-end check for 3
   consecutive cycles of that message, then the instrument cluster shall show the
   takeover request and ACC as not active.

   The safe state of ``SG_ACC_003`` when the ACC ECU cannot reach it itself.

.. aou:: Actuator response
   :id: AOU_ACC_003
   :status: draft
   :derives_from: FSR_ACC_014, FSR_ACC_015
   :asil: C

   The powertrain and brake system shall follow the acceleration request with a response
   no slower than a dead time of 50 ms followed by a first-order lag of 0.4 s.

   A-10. Not assumed: a limit on the request. A wrong request is executed up to +3 and
   −8 m/s² (ADR-003).

.. aou:: Receiver check of the command
   :id: AOU_ACC_004
   :status: draft
   :derives_from: FSR_ACC_017
   :asil: C

   If ``ACC_Cmd`` is missing or fails its end-to-end check for 3 consecutive cycles, then
   the powertrain and brake system shall stop executing ACC requests.

   ADR-000 D-15: the receiver-side check of ``ACC_Cmd``, implemented in the simulated
   plant. A single bad message is discarded.

.. aou:: Request active flag respected
   :id: AOU_ACC_005
   :status: draft
   :derives_from: FSR_ACC_005, FSR_ACC_006, FSR_ACC_014
   :asil: C

   While the request active flag in ``ACC_Cmd`` is cleared, the powertrain and brake
   system shall execute no ACC request.

.. aou:: Pedal signals
   :id: AOU_ACC_006
   :status: draft
   :derives_from: FSR_ACC_006, FSR_ACC_007
   :asil: C

   The vehicle shall report the brake pedal state and the accelerator pedal position in
   the next ``VEH_Dyn`` message after they change, and never report a pressed brake pedal
   as released.

   Brake-signal integrity (ADR-000 D-04). A pedal reported as pressed when it is not
   only ends ACC control, which is the safe direction.

.. aou:: Ego motion signals
   :id: AOU_ACC_007
   :status: draft
   :derives_from: FSR_ACC_010, FSR_ACC_011
   :asil: B

   The vehicle shall report ego speed within ±1 km/h and ego acceleration within
   ±0.3 m/s² of their true values in ``VEH_Dyn``.

   Errors smaller than this are not detectable by the plausibility checks and are not
   relied on. The accuracy is a design value; the tolerance of :need:`FSR_ACC_011`
   (1.0 m/s²) is more than three times the acceleration error.

.. aou:: Radar detection
   :id: AOU_ACC_008
   :status: draft
   :derives_from: FSR_ACC_002, FSR_ACC_012
   :asil: B

   The radar shall report every moving object within 150 m and within ±2.5 m
   of the ego lane centre within 3 cycles of the radar, and report no object where none
   exists.

   Radar plausibility (ADR-000 D-04). A plausible but wrong object defeats doer and
   checker alike, because both read the same radar data (ADR-006).

.. aou:: Radar reports moving objects only
   :id: AOU_ACC_009
   :status: draft
   :derives_from: FSR_ACC_002
   :asil: B

   The radar shall report only objects that have been seen moving.

   ADR-000 D-16 and non-goal "no stationary-object braking": stationary objects are a
   known limitation and the driver's task.

Unintended acceleration or braking within the limits
----------------------------------------------------

*Argument confirmed by pb on 2026-10-06 (ADR-003, consequences); the M4 MIL run checks
the braking claim with a follower model.*

The limit check (:need:`FSR_ACC_001`) removes requests beyond +2.0 and −3.5 m/s² and
steps faster than 2.5 m/s³. A wrong request **within** these limits cannot be told apart
from correct control by a limit check. It remains, and is argued as follows.

- **Braking within A-05 and A-06** (``SG_ACC_002``, ``HE_OS2_M2`` rated C3 at −8 m/s²).
  The deceleration builds at no more than 2.5 m/s³, so reaching −3.5 m/s² takes at least
  1.4 s plus the actuator response, and the brake lights come on at the start. This is
  the profile of a normal ACC braking, which following traffic meets every day. The
  driver ends it with the accelerator (:need:`FSR_ACC_007`) or CANCEL
  (:need:`FSR_ACC_006`). The claim: with this build-up, a follower at a 1 s gap and
  1.5 s reaction time does not collide, so the remainder is controllable (C1 or better)
  rather than C3.
- **Acceleration within A-04** (``SG_ACC_001``). Without a vehicle ahead (``HE_OS1_M1``,
  ASIL A), +2 m/s² beyond the set speed is felt and seen on the speedometer. Once a
  vehicle comes within range, :need:`FSR_ACC_002` blocks it and :need:`FSR_ACC_004` raises
  a fault with a takeover request, at the latest when the time headway falls below
  2.5 s while closing.

Trace from the safety goals
---------------------------

.. needflow::
   :root_id: SG_ACC_001
   :root_direction: incoming
   :root_depth: 2
   :link_types: derives_from

.. needflow::
   :root_id: SG_ACC_002
   :root_direction: incoming
   :root_depth: 2
   :link_types: derives_from

.. needflow::
   :root_id: SG_ACC_003
   :root_direction: incoming
   :root_depth: 2
   :link_types: derives_from

.. needflow::
   :root_id: SG_ACC_004
   :root_direction: incoming
   :root_depth: 2
   :link_types: derives_from

.. needtable::
   :types: fsr
   :columns: id as "ID";title as "Functional safety requirement";asil as "ASIL";derives_from as "Safety goals";allocated_to as "Allocated to"
   :sort: id
   :style: table

.. needtable::
   :types: aou
   :columns: id as "ID";title as "Assumption of use";asil as "ASIL";derives_from as "Derives from"
   :sort: id
   :style: table
