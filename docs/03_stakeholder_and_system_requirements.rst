Stakeholder and system requirements
===================================

:Status: draft, for review by pb
:Applies: ISO 26262-4, clause 6 (system requirements, as input to the technical safety
          concept), and Automotive SPICE SYS.1 / SYS.2, as applied concepts only

Stakeholder needs (``STK_``) say what the driver and the vehicle integrator want from the
ACC. System requirements (``SYS_``) state the nominal behaviour of the item in EARS form
(ADR-005); each one satisfies at least one stakeholder need and is allocated to the
architecture elements in :doc:`07_architecture`. All numeric values are project
assumptions (``A-xx``, :doc:`00_item_definition`), not values from a standard.

**ASIL of system requirements.** ``SYS_`` needs describe the intended function and carry
ASIL QM. Safety integrity is carried by the functional and technical safety requirements
(:doc:`04_functional_safety_concept`, :doc:`05_technical_safety_concept`), which derive
from the safety goals. Where a ``SYS_`` describes behaviour that a safety goal also
requires (for example the brake pedal ending active control), its note names that goal;
the safety requirement, not the ``SYS_``, sets the integrity and the timing that the
safety argument relies on (ADR-005).

Stakeholder needs
-----------------

.. stk:: Keep a set speed with less effort
   :id: STK_ACC_001
   :status: draft

   The driver wants the vehicle to keep a chosen speed on motorways without holding the
   accelerator pedal.

.. stk:: Keep a safe distance to the vehicle ahead
   :id: STK_ACC_002
   :status: draft

   The driver wants the vehicle to slow down for a slower vehicle ahead and to follow it
   at a chosen time gap, and to resume the set speed when the lane is clear.

.. stk:: Stay in control
   :id: STK_ACC_003
   :status: draft

   The driver wants to override or end the ACC at any moment with the pedals or a button,
   and wants the ACC never to act against the driver's braking.

.. stk:: Know what the ACC is doing
   :id: STK_ACC_004
   :status: draft

   The driver wants to see whether the ACC is active, which speed and time gap are set,
   and whether a vehicle ahead is being followed.

.. stk:: Be told when to take over
   :id: STK_ACC_005
   :status: draft

   The driver wants a clear takeover request whenever the ACC stops controlling the
   vehicle without the driver having asked for it, or cannot handle the situation.

.. stk:: Comfortable, bounded control
   :id: STK_ACC_006
   :status: draft

   The driver and passengers want acceleration and braking by the ACC to stay smooth and
   within the limits of a comfort function; emergency braking is the driver's task.

.. stk:: Fit the vehicle architecture
   :id: STK_ACC_007
   :status: draft

   The vehicle integrator wants the ACC ECU to exchange data only through the defined CAN
   messages, to detect corrupted or missing messages, and to run on a 10 ms task cycle.

Modes and transitions
---------------------

The transition rules below are evaluated in a fixed priority order, first match wins, at
most one transition per 10 ms cycle (ADR-000 D-11): main switch off, fault, brake pedal
or CANCEL, speed below 25 km/h, accelerator override, then speed/follow arbitration.

.. sys:: Transition priority
   :id: SYS_ACC_001
   :status: draft
   :satisfies: STK_ACC_003
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When more than one mode transition condition holds in the same 10 ms cycle, the ACC
   system shall take only the transition with the highest priority, in the order main
   switch off, fault, brake pedal or CANCEL, speed below 25 km/h, accelerator override,
   speed/follow arbitration.

   At most one transition per cycle. The same order drives the SysML state machine (M3),
   the MIL reference (M4) and the C implementation (M5).

.. sys:: Main switch on
   :id: SYS_ACC_002
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_HMI, ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver switches the main switch on while the ACC system is in OFF, the ACC
   system shall change to STANDBY within 100 ms.

.. sys:: Main switch off
   :id: SYS_ACC_003
   :status: draft
   :satisfies: STK_ACC_003
   :allocated_to: ARC_HMI, ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver switches the main switch off, the ACC system shall change to OFF from
   any mode within 100 ms.

.. sys:: Activation with SET
   :id: SYS_ACC_004
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_HMI, ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver presses SET while the ACC system is in STANDBY with ego speed within
   30–150 km/h, no fault reported, all input messages received at least once and the brake
   pedal not pressed, the ACC system shall store the current ego speed as set speed and
   change to ACTIVE_SPEED within 100 ms.

   Activation range A-01. Inputs that were never received inhibit activation without a
   fault (ADR-000 D-13).

.. sys:: Activation with RESUME
   :id: SYS_ACC_005
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_HMI, ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver presses RESUME while the ACC system is in STANDBY with a stored set
   speed, ego speed within 30–150 km/h, no fault reported, all input messages received at
   least once and the brake pedal not pressed, the ACC system shall change to
   ACTIVE_SPEED with the stored set speed within 100 ms.

.. sys:: RESUME without stored set speed
   :id: SYS_ACC_006
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_HMI, ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver presses RESUME while no set speed is stored, the ACC system shall stay
   in its current mode.

   Gap-filler from ADR-000 D-11. The set speed is cleared when the main switch is
   switched off.

.. sys:: Activation blocked outside the speed range
   :id: SYS_ACC_007
   :status: draft
   :satisfies: STK_ACC_001, STK_ACC_004
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver presses SET or RESUME while ego speed is below 30 km/h or above
   150 km/h, the ACC system shall stay in STANDBY.

   Above 150 km/h only activation is blocked; an active ACC stays active
   (:need:`SYS_ACC_012`).

.. sys:: Speed and follow arbitration
   :id: SYS_ACC_008
   :status: draft
   :satisfies: STK_ACC_002
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   While the ACC system is in ACTIVE_SPEED or ACTIVE_FOLLOW, the ACC system shall be in
   ACTIVE_FOLLOW when a relevant target is selected and the gap control demands less
   acceleration than the speed control, and in ACTIVE_SPEED otherwise.

   Arbitration ``a_raw = min(a_v, a_d)``; the mode shows which law is in effect.

.. sys:: Accelerator override
   :id: SYS_ACC_009
   :status: draft
   :satisfies: STK_ACC_003
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the accelerator pedal position exceeds 5 % while the ACC system is in ACTIVE_SPEED
   or ACTIVE_FOLLOW, the ACC system shall change to OVERRIDE and clear the request active
   flag within 100 ms.

   Override threshold A-12. In OVERRIDE the driver's pedal commands the powertrain.

.. sys:: End of override
   :id: SYS_ACC_010
   :status: draft
   :satisfies: STK_ACC_003
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the accelerator pedal position falls to 5 % or less while the ACC system is in
   OVERRIDE with ego speed at or above 25 km/h, the ACC system shall return to the active
   mode it left and resume control within 100 ms.

   Below 25 km/h the release leads to STANDBY with a TOR instead
   (:need:`SYS_ACC_014`).

.. sys:: Brake pedal or CANCEL ends active control
   :id: SYS_ACC_011
   :status: draft
   :satisfies: STK_ACC_003
   :allocated_to: ARC_HMI, ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the driver presses the brake pedal or CANCEL while the ACC system is in
   ACTIVE_SPEED, ACTIVE_FOLLOW or OVERRIDE, the ACC system shall change to STANDBY and clear
   the request active flag within 100 ms.

   Safety-relevant: ``SG_ACC_004`` (ASIL B, FTTI 500 ms). The integrity of this behaviour
   is required by the functional safety concept, not by this requirement.

.. sys:: High speed while active
   :id: SYS_ACC_012
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   While the ACC system is active and ego speed is above 150 km/h, the ACC system shall
   stay active and control ego speed toward the set speed.

   Gap-filler from ADR-000 D-11. The set speed is at most 150 km/h, so the ACC decelerates.

.. sys:: Deactivation below 25 km/h
   :id: SYS_ACC_013
   :status: draft
   :satisfies: STK_ACC_005
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When ego speed falls below 25 km/h while the ACC system is in ACTIVE_SPEED or
   ACTIVE_FOLLOW, the ACC system shall change to STANDBY and raise the takeover request
   within 100 ms.

   A-01; no stop and go. Scenario 10. The request is ramped to 0 m/s² at the jerk limit
   (:need:`SYS_ACC_024`).

.. sys:: Override released below 25 km/h
   :id: SYS_ACC_014
   :status: draft
   :satisfies: STK_ACC_005
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the accelerator pedal position falls to 5 % or less while the ACC system is in
   OVERRIDE with ego speed below 25 km/h, the ACC system shall change to STANDBY and raise
   the takeover request within 100 ms.

   Gap-filler from ADR-000 D-11.

.. sys:: Fault while active
   :id: SYS_ACC_015
   :status: draft
   :satisfies: STK_ACC_005
   :allocated_to: ARC_ACC_CTRL, ARC_ACC_MON
   :asil: QM
   :verification_method: test

   When the monitor reports a fault while the ACC system is in ACTIVE_SPEED, ACTIVE_FOLLOW
   or OVERRIDE, the ACC system shall change to FAULT and raise the takeover request within
   100 ms.

   ADR-000 D-10, D-13. ``AccMon`` reaches the safe state on its own; the FAULT mode of
   ``AccCtrl`` keeps the mode display consistent. Timing against each FTTI is set by the
   safety requirements.

.. sys:: Fault while not active
   :id: SYS_ACC_016
   :status: draft
   :satisfies: STK_ACC_004
   :allocated_to: ARC_ACC_CTRL, ARC_ACC_MON
   :asil: QM
   :verification_method: test

   When the monitor reports a fault while the ACC system is in STANDBY, the ACC system
   shall change to FAULT without a takeover request within 100 ms.

   ADR-000 D-13: shown to the driver as "ACC unavailable"; activation is blocked.

.. sys:: Leaving FAULT
   :id: SYS_ACC_017
   :status: draft
   :satisfies: STK_ACC_003, STK_ACC_005
   :allocated_to: ARC_HMI, ARC_ACC_CTRL, ARC_ACC_MON
   :asil: QM
   :verification_method: test

   When the driver presses CANCEL while the ACC system is in FAULT and the monitor reports
   no fault, the ACC system shall change to STANDBY within 100 ms.

   The monitor clears its latched fault under the same condition (ADR-000 D-10).

.. sys:: Startup
   :id: SYS_ACC_018
   :status: draft
   :satisfies: STK_ACC_007
   :allocated_to: ARC_ACC_CTRL, ARC_ACC_MON
   :asil: QM
   :verification_method: test

   When the ACC ECU starts, the ACC system shall be in OFF and treat every input message as
   never received.

   ADR-000 D-13: a message that was never received inhibits activation but is not a fault.

HMI
---

.. sys:: Button debouncing
   :id: SYS_ACC_019
   :status: draft
   :satisfies: STK_ACC_003, STK_ACC_007
   :allocated_to: ARC_HMI
   :asil: QM
   :verification_method: test

   When a button signal in ``HMI_Btn`` changes from released to pressed in 2 consecutive
   messages, the ACC system shall accept one press of that button.

   ``HMI_Btn`` has a 20 ms cycle, so a press is accepted after 20–40 ms. Holding a button
   does not repeat it. The debounce count is a design value, not a safety value.

.. sys:: Time gap selection
   :id: SYS_ACC_020
   :status: draft
   :satisfies: STK_ACC_002
   :allocated_to: ARC_HMI
   :asil: QM
   :verification_method: test

   When the driver presses gap + or gap −, the ACC system shall select the next longer or
   shorter time gap out of 1.0, 1.5 or 2.0 s, staying at the longest or shortest one at
   the end of the range.

   A-02. The default after the main switch is switched on is 1.5 s.

.. sys:: Mode display
   :id: SYS_ACC_021
   :status: draft
   :satisfies: STK_ACC_004
   :allocated_to: ARC_ACC_CTRL, ARC_COM
   :asil: QM
   :verification_method: test

   The ACC system shall send its mode, set speed, selected time gap and target detected
   flag in ``ACC_Status`` every 100 ms.

   Safety-relevant: a wrong mode display is part of malfunction M3 (``SG_ACC_003``,
   ADR-003).

.. sys:: Takeover request signal
   :id: SYS_ACC_022
   :status: draft
   :satisfies: STK_ACC_005
   :allocated_to: ARC_ACC_MON, ARC_COM
   :asil: QM
   :verification_method: test

   The ACC system shall send the takeover request flag in ``ACC_Cmd`` every 10 ms.

   ``AccMon`` owns ``ACC_Cmd`` (ADR-000 D-10). How fast the cluster shows the TOR is an
   assumption of use (:doc:`04_functional_safety_concept`).

Speed and gap control
---------------------

.. sys:: Speed control accuracy
   :id: SYS_ACC_023
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   While the ACC system is in ACTIVE_SPEED on a level road in steady state, the ACC system
   shall hold ego speed within ±2 km/h of the set speed.

   Steady state: set speed unchanged for at least 10 s. Scenario 1.

.. sys:: Request ramp at low-speed deactivation
   :id: SYS_ACC_024
   :status: draft
   :satisfies: STK_ACC_006
   :allocated_to: ARC_ACC_MON
   :asil: QM
   :verification_method: test

   When the ACC system changes to STANDBY because ego speed fell below 25 km/h, the ACC
   system shall ramp the acceleration request to 0 m/s² at no more than 2.5 m/s³ before it
   clears the request active flag.

   A braking request is not dropped at once while the driver takes over after the TOR.
   On the brake pedal or CANCEL the request active flag is cleared at once
   (:need:`SYS_ACC_011`, ``SG_ACC_004``); the safe states of the safety goals are set in
   :doc:`02_safety_goals`.

.. sys:: Set speed adjustment
   :id: SYS_ACC_025
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_HMI
   :asil: QM
   :verification_method: test

   When the driver presses SET while the ACC system is active, the ACC system shall
   decrease the set speed by 5 km/h, and not below 30 km/h.

   RESUME while active increases it by 5 km/h, up to 150 km/h (:need:`SYS_ACC_026`).

.. sys:: Set speed increase
   :id: SYS_ACC_026
   :status: draft
   :satisfies: STK_ACC_001
   :allocated_to: ARC_HMI
   :asil: QM
   :verification_method: test

   When the driver presses RESUME while the ACC system is active, the ACC system shall
   increase the set speed by 5 km/h, and not above 150 km/h.

.. sys:: Target selection
   :id: SYS_ACC_027
   :status: draft
   :satisfies: STK_ACC_002
   :allocated_to: ARC_TGT_SEL
   :asil: QM
   :verification_method: test

   While the ACC system is active, the ACC system shall select as relevant target the
   closest valid radar object whose lateral offset is within ±1.8 m of the ego lane
   centre.

   Straight roads only (non-goal). Hysteresis on selection and loss of a target is a
   software design detail (M5). The lateral band is a design value; the monitor uses its
   own, wider band (ADR-000 D-06).

.. sys:: Gap control
   :id: SYS_ACC_028
   :status: draft
   :satisfies: STK_ACC_002
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   While the ACC system is in ACTIVE_FOLLOW behind a lead vehicle at constant speed in
   steady state, the ACC system shall hold the distance within ±10 % of the desired
   distance 5 m plus the selected time gap times ego speed.

   Spacing policy ``d_des = d_0 + t_gap · v_ego`` with A-02, A-03. Steady state: lead
   speed constant for at least 15 s. Scenarios 2 and 3. The tolerance is a design value
   to be confirmed by MIL tuning (M4, ADR).

.. sys:: Return to set speed
   :id: SYS_ACC_029
   :status: draft
   :satisfies: STK_ACC_002
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   When the relevant target is lost while the ACC system is in ACTIVE_FOLLOW, the ACC
   system shall change to ACTIVE_SPEED and control ego speed toward the set speed.

   Scenario 7 (cut-out).

Limits
------

.. sys:: Acceleration request limits
   :id: SYS_ACC_030
   :status: draft
   :satisfies: STK_ACC_006
   :allocated_to: ARC_ACC_CTRL, ARC_ACC_MON
   :asil: QM
   :verification_method: test

   The ACC system shall keep its acceleration request within −3.5 to +2.0 m/s².

   A-04, A-05. Safety-relevant: the monitor enforces the limits as a safety mechanism
   (:doc:`04_functional_safety_concept`).

.. sys:: Jerk limit
   :id: SYS_ACC_031
   :status: draft
   :satisfies: STK_ACC_006
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   While the ACC system is in ACTIVE_SPEED or ACTIVE_FOLLOW, the ACC system shall change
   its acceleration request by no more than 2.5 m/s³.

   A-06, a comfort limit. The safe states of ``SG_ACC_001`` and ``SG_ACC_002`` cut or limit
   the request faster than this.

.. sys:: TOR at the deceleration limit
   :id: SYS_ACC_032
   :status: draft
   :satisfies: STK_ACC_005, STK_ACC_006
   :allocated_to: ARC_ACC_CTRL
   :asil: QM
   :verification_method: test

   While the gap control demands a deceleration beyond −3.5 m/s² for more than 200 ms, the
   ACC system shall request −3.5 m/s² and raise the takeover request.

   Scenario 5: the ACC saturates at A-05 and asks the driver to brake. It is not an
   emergency braking function. The 200 ms filter is a design value against single-cycle
   peaks.

.. sys:: No request outside active modes
   :id: SYS_ACC_033
   :status: draft
   :satisfies: STK_ACC_003
   :allocated_to: ARC_ACC_MON
   :asil: QM
   :verification_method: test

   While the ACC system is in OFF, STANDBY, OVERRIDE or FAULT, the ACC system shall send
   the request active flag cleared, except during the ramp of :need:`SYS_ACC_024` or the
   safe state reaction of the monitor.

Communication
-------------

.. sys:: Cyclic execution
   :id: SYS_ACC_034
   :status: draft
   :satisfies: STK_ACC_007
   :allocated_to: ARC_SCHED
   :asil: QM
   :verification_method: test

   The ACC system shall run its receive, control, monitor and transmit functions once
   every 10 ms in a fixed order.

   A-07; order from ADR-000 D-14.

.. sys:: Command message
   :id: SYS_ACC_035
   :status: draft
   :satisfies: STK_ACC_007
   :allocated_to: ARC_COM, ARC_E2E, ARC_CANIF
   :asil: QM
   :verification_method: test

   The ACC system shall send ``ACC_Cmd`` every 10 ms with an alive counter and a CRC-8.

.. sys:: Input end-to-end check
   :id: SYS_ACC_036
   :status: draft
   :satisfies: STK_ACC_007
   :allocated_to: ARC_E2E
   :asil: QM
   :verification_method: test

   When a received ``RDR_Obj1..4``, ``VEH_Dyn`` or ``HMI_Btn`` message has a wrong CRC-8,
   or an alive counter that is repeated or skips a value, the ACC system shall discard
   that message and keep the last valid value.

   ADR-000 D-15. A fault after consecutive errors and timeouts (A-11) are safety
   mechanisms in :doc:`04_functional_safety_concept`.

.. sys:: Input timeout
   :id: SYS_ACC_037
   :status: draft
   :satisfies: STK_ACC_007
   :allocated_to: ARC_COM, ARC_ACC_MON
   :asil: QM
   :verification_method: test

   If a received message that was received at least once is missing for 3 consecutive
   cycles of that message, then the ACC system shall report a fault.

   A-11; ADR-000 D-13.

Traceability
------------

.. needtable::
   :types: stk
   :columns: id as "ID";title as "Stakeholder need";satisfies_back as "Satisfied by"
   :sort: id
   :style: table

.. needtable::
   :types: sys
   :columns: id as "ID";title as "System requirement";satisfies as "Satisfies";allocated_to as "Allocated to";verification_method as "Verification"
   :sort: id
   :style: table
