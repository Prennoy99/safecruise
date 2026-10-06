Technical safety concept
========================

:Status: draft, for review by pb. Values marked ``⟨pb: …⟩`` are set by pb (ADR-000 D-17);
         the ASILs of decomposed requirements follow ADR-006.
:Applies: ISO 26262-4, clause 6 (technical safety concept), and ISO 26262-9, clause 5
          (ASIL decomposition), as applied concepts only

The technical safety requirements (``TSR_``) allocate each functional safety requirement
of :doc:`04_functional_safety_concept` to the elements of :doc:`07_architecture`. Where a
safety requirement is met by both the controller (doer) and the monitor (checker), it is
split into one ``TSR_`` per side with decomposed ASILs, such as ``QM(C)`` for ``AccCtrl``
and ``C(C)`` for ``AccMon`` (ADR-006). Safety mechanisms that only the monitor has keep the
full ASIL.

Rules that hold for all ``TSR_`` of ``AccMon``:

- one 10 ms cycle: the monitor runs after the controller and before transmission, on the
  inputs of the same cycle (ADR-000 D-14);
- "latch a fault" means :need:`FSR_ACC_013` applies, and the reaction of
  :need:`TSR_ACC_017`, :need:`TSR_ACC_018` and :need:`TSR_ACC_019` follows in the same
  cycle;
- the monitor and the controller compute the block condition of :need:`FSR_ACC_002` with
  the same formula on the same inputs, so a healthy controller never trips
  :need:`TSR_ACC_005`.

Request limits
--------------

.. tsr:: Controller output limits
   :id: TSR_ACC_001
   :status: draft
   :derives_from: FSR_ACC_001
   :allocated_to: ARC_ACC_CTRL
   :asil: ⟨pb: ADR-006⟩
   :verification_method: test

   The AccCtrl component shall limit its proposed acceleration request to −3.5 to
   +2.0 m/s² and its change to 0.025 m/s² per 10 ms cycle.

   Doer side of the decomposition of :need:`FSR_ACC_001`. 0.025 m/s² per cycle is A-06.

.. tsr:: Monitor limit and jerk check
   :id: TSR_ACC_002
   :status: draft
   :derives_from: FSR_ACC_001
   :allocated_to: ARC_ACC_MON
   :asil: ⟨pb: ADR-006⟩
   :verification_method: test

   If the proposed acceleration request read by the AccMon component is not a number, is
   outside −3.5 to +2.0 m/s², or differs from the proposed request of the previous cycle
   by more than 0.026 m/s², then the AccMon component shall latch a fault.

   Checker side of the decomposition of :need:`FSR_ACC_001`. The jerk check allows
   0.001 m/s² per cycle above A-06 for float32 rounding, so a controller that rate-limits
   at exactly A-06 never trips it.

Acceleration block
------------------

.. tsr:: Monitor acceleration block
   :id: TSR_ACC_003
   :status: draft
   :derives_from: FSR_ACC_002, FSR_ACC_003
   :allocated_to: ARC_ACC_MON
   :asil: ⟨pb: ADR-006⟩
   :verification_method: test

   While the condition of :need:`FSR_ACC_002` holds for any object of the raw radar object
   list, or held within the last ⟨pb: T_hold⟩ ms, the AccMon component shall send an
   acceleration request of at most 0 m/s².

   Checker side. The raw list, not the target from ``TgtSel`` (ADR-000 D-06).

.. tsr:: Controller acceleration block
   :id: TSR_ACC_004
   :status: draft
   :derives_from: FSR_ACC_002, FSR_ACC_003
   :allocated_to: ARC_ACC_CTRL
   :asil: ⟨pb: ADR-006⟩
   :verification_method: test

   While the condition of :need:`FSR_ACC_002` holds for any object of the raw radar object
   list, or held within the last ⟨pb: T_hold⟩ ms, the AccCtrl component shall propose an
   acceleration request of at most 0 m/s².

   Doer side. Applying the monitor's rule in the controller as well keeps a healthy
   controller from tripping :need:`TSR_ACC_005`; adjacent-lane objects then reduce
   availability only (ADR-000 D-06, ADR-008).

.. tsr:: Positive request against the block
   :id: TSR_ACC_005
   :status: draft
   :derives_from: FSR_ACC_004
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If the AccMon component reads a positive proposed acceleration request while
   :need:`TSR_ACC_003` blocks positive acceleration, then the AccMon component shall latch
   a fault.

Driver precedence and activation
--------------------------------

.. tsr:: Monitor activation record
   :id: TSR_ACC_006
   :status: draft
   :derives_from: FSR_ACC_005
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   The AccMon component shall set the request active flag only while it has read SET or
   RESUME pressed in ``HMI_Btn`` later than the last brake pedal pressed in ``VEH_Dyn``,
   CANCEL pressed, main switch off, latched fault and its own initialisation.

   The monitor reads the raw button and pedal signals, not ``Hmi``. The record is also
   the monitor's view of "ACC engaged" for :need:`TSR_ACC_019`. Known weakness: a SET
   press that the controller ignores (for example below 30 km/h) still enables the
   monitor until the next brake pedal or CANCEL press.

.. tsr:: Monitor brake pedal and CANCEL
   :id: TSR_ACC_007
   :status: draft
   :derives_from: FSR_ACC_006
   :allocated_to: ARC_ACC_MON
   :asil: ⟨pb: ADR-006⟩
   :verification_method: test

   When the AccMon component reads the brake pedal pressed in ``VEH_Dyn`` or CANCEL
   pressed in ``HMI_Btn``, the AccMon component shall clear the request active flag in the
   same cycle.

   Checker side. No debouncing: a single CANCEL message is enough. A false CANCEL only
   ends ACC control; debouncing would use up 20 ms of a budget that has 20 ms margin.

.. tsr:: Controller brake pedal and CANCEL
   :id: TSR_ACC_008
   :status: draft
   :derives_from: FSR_ACC_006
   :allocated_to: ARC_ACC_CTRL, ARC_HMI
   :asil: ⟨pb: ADR-006⟩
   :verification_method: test

   When the AccCtrl component reads the brake pedal pressed or a CANCEL press, the AccCtrl
   component shall change to STANDBY and propose no request in the same cycle.

   Doer side; :need:`SYS_ACC_011`.

.. tsr:: Monitor accelerator pedal
   :id: TSR_ACC_009
   :status: draft
   :derives_from: FSR_ACC_007
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   While the AccMon component reads an accelerator pedal position above 5 % in
   ``VEH_Dyn``, the AccMon component shall send the request active flag cleared.

Input integrity
---------------

.. tsr:: End-to-end check of received messages
   :id: TSR_ACC_010
   :status: draft
   :derives_from: FSR_ACC_008
   :allocated_to: ARC_E2E
   :asil: B
   :verification_method: test

   When a received ``RDR_Obj1..4``, ``VEH_Dyn`` or ``HMI_Btn`` message fails its CRC-8 or
   alive counter check in ⟨pb: N_e2e⟩ consecutive messages, the E2E component shall
   report an end-to-end fault for that message.

   ADR-000 D-15: CRC-8 SAE J1850 over payload, alive counter and data ID; a repeated or
   skipped counter is an error.

.. tsr:: Message age
   :id: TSR_ACC_011
   :status: draft
   :derives_from: FSR_ACC_009
   :allocated_to: ARC_RTE
   :asil: B
   :verification_method: test

   The RTE shall provide for each received message a flag that it was received at least
   once and the number of 10 ms cycles since its last valid reception.

   ADR-000 D-14.

.. tsr:: Monitor input faults
   :id: TSR_ACC_012
   :status: draft
   :derives_from: FSR_ACC_008, FSR_ACC_009
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If the E2E component reports an end-to-end fault, or a message that was received at
   least once is older than 3 cycles of that message, then the AccMon component shall
   latch a fault.

   A-11: 150 ms for ``RDR_Obj1..4``, 30 ms for ``VEH_Dyn``, 60 ms for ``HMI_Btn``.

.. tsr:: Monitor plausibility checks
   :id: TSR_ACC_013
   :status: draft
   :derives_from: FSR_ACC_010
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If the AccMon component reads a value that violates :need:`FSR_ACC_010`, then the
   AccMon component shall latch a fault in the cycle in which the message arrives.

   Limits ⟨pb: jump limits⟩ and ⟨pb: speed consistency limit⟩ are defined in
   :need:`FSR_ACC_010`.

Deceleration and takeover
-------------------------

.. tsr:: Requested against measured deceleration
   :id: TSR_ACC_014
   :status: draft
   :derives_from: FSR_ACC_011
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   If the measured ego acceleration exceeds the negative request sent by the AccMon
   component, delayed by 50 ms and filtered by a first-order lag of 0.4 s, by more than
   ⟨pb: a_tol⟩ m/s² for longer than ⟨pb: t_tol⟩ ms, then the AccMon component shall latch
   a fault.

   A-10 model of the actuator response (:need:`AOU_ACC_003`).

.. tsr:: Monitor takeover request at short time-to-collision
   :id: TSR_ACC_015
   :status: draft
   :derives_from: FSR_ACC_012
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   While its activation record (:need:`TSR_ACC_006`) is set and the condition of
   :need:`FSR_ACC_012` holds for any object of the raw radar object list, the AccMon
   component shall set the takeover request flag in ``ACC_Cmd``.

Fault reaction
--------------

.. tsr:: Fault latch and release
   :id: TSR_ACC_016
   :status: draft
   :derives_from: FSR_ACC_013
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   When the AccMon component latches a fault, the AccMon component shall ignore the
   proposed request and keep the fault until no fault condition holds and it reads CANCEL
   pressed in ``HMI_Btn``.

.. tsr:: Positive request at a fault
   :id: TSR_ACC_017
   :status: draft
   :derives_from: FSR_ACC_014
   :allocated_to: ARC_ACC_MON
   :asil: B
   :verification_method: test

   When the AccMon component latches a fault while the request it sent in the previous
   cycle is positive, the AccMon component shall send 0 m/s² and the request active flag
   cleared in the same cycle.

.. tsr:: Negative request at a fault
   :id: TSR_ACC_018
   :status: draft
   :derives_from: FSR_ACC_015
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   When the AccMon component latches a fault while the request it sent in the previous
   cycle is negative, the AccMon component shall send that request limited to −3.5 m/s²,
   raise it toward 0 m/s² by 0.025 m/s² per 10 ms cycle, and clear the request active flag
   when it reaches 0 m/s².

.. tsr:: Takeover request and mode at a fault
   :id: TSR_ACC_019
   :status: draft
   :derives_from: FSR_ACC_016
   :allocated_to: ARC_ACC_MON
   :asil: C
   :verification_method: test

   When the AccMon component latches a fault while its activation record
   (:need:`TSR_ACC_006`) is set, the AccMon component shall set the takeover request flag
   in ``ACC_Cmd`` and write FAULT as the mode in ``ACC_Status`` in the same cycle, until the
   fault is released.

   The monitor overrides the mode written by ``AccCtrl``, so the mode display does not
   depend on the doer (``SG_ACC_003``; extends ADR-000 D-10, see ADR-006).

Output path
-----------

.. tsr:: End-to-end protection of the outputs
   :id: TSR_ACC_020
   :status: draft
   :derives_from: FSR_ACC_017
   :allocated_to: ARC_E2E
   :asil: C
   :verification_method: test

   The E2E component shall protect ``ACC_Cmd`` and ``ACC_Status`` with a CRC-8 and an alive
   counter that it advances only in cycles in which the AccMon component has completed.

.. tsr:: Cyclic execution of the monitor
   :id: TSR_ACC_021
   :status: draft
   :derives_from: FSR_ACC_013, FSR_ACC_017
   :allocated_to: ARC_SCHED
   :asil: C
   :verification_method: test

   The scheduler shall run the AccMon runnable once every 10 ms, after the AccCtrl
   runnable and before the transmission of ``ACC_Cmd``.

   No timing supervision of the scheduler exists; a stalled scheduler is detected by the
   receivers through the alive counter (:need:`AOU_ACC_002`, :need:`AOU_ACC_004`).

.. tsr:: Monitor outputs through the RTE
   :id: TSR_ACC_022
   :status: draft
   :derives_from: FSR_ACC_017
   :allocated_to: ARC_RTE
   :asil: C
   :verification_method: test

   The RTE shall pass the outputs written by the AccMon component to the E2E protection
   unchanged in the same cycle.

.. tsr:: Read-back of the packed command
   :id: TSR_ACC_023
   :status: draft
   :derives_from: FSR_ACC_017
   :allocated_to: ARC_E2E
   :asil: C
   :verification_method: test

   If the values unpacked from the packed ``ACC_Cmd`` or ``ACC_Status`` payload differ
   from the values written by the AccMon component, then the E2E component shall not
   protect that payload, so that the receivers discard it.

   Proposed in ADR-007: COM packing stays QM under a read-back check.

.. tsr:: Round-trip check of received messages
   :id: TSR_ACC_024
   :status: draft
   :derives_from: FSR_ACC_008
   :allocated_to: ARC_E2E
   :asil: B
   :verification_method: test

   If the signals unpacked by COM from a received message do not pack back to the payload
   that passed its end-to-end check, then the E2E component shall count the message as an
   end-to-end error.

   Proposed in ADR-007: COM unpacking stays QM under a round-trip check.

Time budget against the FTTI
----------------------------

Each row is one fault and the mechanism that handles it. Convention: the time counts from
the fault until the actuator has removed the wrong request, taken as the actuator dead time
(50 ms) plus one time constant of its lag (400 ms), A-10. CAN transmission time is below
1 ms and is not counted. Detection counts the message cycle in which the fault first
shows. These are design figures; the FTTI experiment in M4 measures them.

.. list-table::
   :header-rows: 1
   :widths: 18 30 12 12 14 14

   * - Safety goal (FTTI)
     - Fault and mechanism
     - Detection
     - ECU reaction
     - Actuator or display
     - Total
   * - ``SG_ACC_001`` (1000 ms)
     - Request above +2.0 m/s² or too steep (:need:`TSR_ACC_002`)
     - 10 ms
     - 10 ms
     - 450 ms
     - 470 ms
   * - ``SG_ACC_001`` (1000 ms)
     - Controller accelerates toward a close object (:need:`TSR_ACC_005`)
     - 10 ms after the block condition holds
     - 10 ms
     - 450 ms
     - 470 ms
   * - ``SG_ACC_001`` (1000 ms)
     - Corrupted or lost radar messages (:need:`TSR_ACC_012`)
     - ⟨pb: N_e2e⟩ × 50 ms, timeout 150 ms
     - 10 ms
     - 450 ms
     - 610 ms with 3 errors
   * - ``SG_ACC_002`` (500 ms)
     - Request below −3.5 m/s² or too steep (:need:`TSR_ACC_002`)
     - in the cycle
     - limited value sent in the same cycle
     - none
     - 0 ms
   * - ``SG_ACC_002`` (500 ms)
     - Braking within A-05 ended by the driver's accelerator pedal (:need:`TSR_ACC_009`)
     - 10 ms
     - 10 ms
     - 450 ms
     - 470 ms
   * - ``SG_ACC_003`` (1000 ms)
     - Too little deceleration (:need:`TSR_ACC_014`)
     - 50 ms + ⟨pb: t_tol⟩ ms
     - 10 ms
     - ⟨pb: TOR latency⟩ ms
     - 60 ms + ⟨pb: t_tol⟩ + ⟨pb: TOR latency⟩
   * - ``SG_ACC_003`` (1000 ms)
     - ACC ECU silent or monitor stalled (:need:`AOU_ACC_002`)
     - 30 ms (``ACC_Cmd`` × 3)
     - none
     - ⟨pb: TOR latency⟩ ms
     - 30 ms + ⟨pb: TOR latency⟩
   * - ``SG_ACC_004`` (500 ms)
     - Brake pedal while ACC requests (:need:`TSR_ACC_007`)
     - 10 ms
     - 10 ms
     - 450 ms
     - 470 ms
   * - ``SG_ACC_004`` (500 ms)
     - CANCEL while ACC requests (:need:`TSR_ACC_007`)
     - 20 ms
     - 10 ms
     - 450 ms
     - 480 ms

The tightest rows are ``SG_ACC_004`` and the accelerator row of ``SG_ACC_002``, with
20–30 ms margin. Almost all of it is the actuator lag, which this project cannot change;
the ECU part is 20–30 ms.

Communication: black channel
----------------------------

``COM`` and ``CanIf`` are QM. Corruption, repetition, loss, delay and masquerading of
messages between the E2E component and the bus are detected by the end-to-end protection
(CRC-8 with data ID, alive counter, timeout), so these elements are a black channel. The
argument, its limits and the read-back checks of :need:`TSR_ACC_023` and
:need:`TSR_ACC_024` are in ADR-007.

Trace from the safety goals
---------------------------

.. needflow::
   :root_id: SG_ACC_001
   :root_direction: incoming
   :link_types: derives_from

.. needflow::
   :root_id: SG_ACC_002
   :root_direction: incoming
   :link_types: derives_from

.. needflow::
   :root_id: SG_ACC_003
   :root_direction: incoming
   :link_types: derives_from

.. needflow::
   :root_id: SG_ACC_004
   :root_direction: incoming
   :link_types: derives_from

.. needtable::
   :types: tsr
   :columns: id as "ID";title as "Technical safety requirement";asil as "ASIL";derives_from as "Derives from";allocated_to as "Allocated to"
   :sort: id
   :style: table
