Item definition
===============

:Status: draft, for review by pb
:Applies: ISO 26262-3, clause 5 (item definition), as applied concepts only

This page defines the item that the hazard analysis (:doc:`01_hara`) is done on: what it
does, where its boundary is, what it exchanges with its environment, and what it relies on.
All numeric values are project assumptions (``A-xx``), not values from a standard.

Function
--------

SafeCruise is an Adaptive Cruise Control (ACC) for motorways and similar roads. It is a
driver-assistance function at SAE J3016 Level 1: it controls longitudinal motion only, and
the driver supervises it at all times and stays responsible for driving.

When active, the ACC

- holds a speed set by the driver when no relevant vehicle is ahead;
- follows a slower vehicle ahead at a time gap selected by the driver;
- limits its own authority: bounded acceleration, deceleration and jerk;
- hands control back to the driver with a takeover request (TOR) when it reaches its
  limits or detects a fault.

The driver can override the ACC at any time: the accelerator pedal overrides it
temporarily, the brake pedal and the CANCEL button end active control.

Item boundary
-------------

The item is the vehicle-level ACC function. The hazard analysis is done at this level.
Development in this repository covers only the software of the ACC ECU. The radar sensor,
the powertrain and brake actuation, and the HMI hardware are outside the scope of
implementation; they are simulated, and what the item relies on from them is recorded as
assumptions (see `Assumptions on elements outside the ACC ECU`_).

::

           ┌───────────── ITEM: Adaptive Cruise Control ──────────────┐
           │                                                           │
    Radar ─┼─► CAN ─► ┌──────────── ACC ECU (implemented) ───────────┐ │
    (sim)  │          │ TgtSel ─► AccCtrl (doer) ─► AccMon (checker) │─┼─► CAN ─► Powertrain/Brake
  Vehicle ─┼─► CAN ─► │ Hmi ─────┘                                   │ │          (sim plant)
    (sim)  │          └──────────────────────────────────────────────┘ │
      HMI ─┼─► CAN ─►                                    ACC_Status ───┼─► Cluster (sim)
    (sim)  └───────────────────────────────────────────────────────────┘

.. list-table:: Elements
   :header-rows: 1
   :widths: 22 14 64

   * - Element
     - In this repo
     - Role
   * - ACC ECU software (``Hmi``, ``TgtSel``, ``AccCtrl``, ``AccMon``, RTE, COM, E2E,
       CanIf, scheduler)
     - implemented
     - Button handling, target selection, mode logic and control law (doer), independent
       monitor that owns the output command (checker)
   * - Radar sensor
     - simulated
     - Up to 4 moving objects with range, range rate and lateral offset
   * - Powertrain and brake actuation
     - simulated
     - Executes the acceleration request; reports ego speed, acceleration and pedals
   * - HMI (buttons) and instrument cluster
     - simulated
     - Driver commands in; mode, set speed, time gap, target and TOR out

Outside the item: the driver, other road users, the road and its environment, and vehicle
functions that act independently of ACC (service brake by pedal, steering, any emergency
braking function; this project has none, see `Known limitations`_).

Interfaces
----------

All interfaces of the ACC ECU are CAN messages. Every message carries a 4-bit alive
counter and a CRC-8; the receiver checks both (end-to-end protection). Signal scaling and
ranges are fixed with the CAN database in M5.

.. list-table:: CAN interfaces
   :header-rows: 1
   :widths: 16 12 10 62

   * - Message
     - Direction
     - Cycle
     - Content
   * - ``RDR_Obj1..4``
     - in (radar)
     - 50 ms
     - Range, range rate, lateral offset, object ID, valid flag
   * - ``VEH_Dyn``
     - in (vehicle)
     - 10 ms
     - Ego speed, ego acceleration, brake pedal pressed, accelerator pedal position
   * - ``HMI_Btn``
     - in (HMI)
     - 20 ms
     - Main switch, SET, RESUME, CANCEL, gap +, gap −
   * - ``ACC_Cmd``
     - out (actuation)
     - 10 ms
     - Acceleration request, request active, TOR
   * - ``ACC_Status``
     - out (cluster)
     - 100 ms
     - Mode, set speed, time gap, target detected

The driver interacts with the item through the buttons and pedals (in) and the cluster
display, including the TOR (out). ``SIM_Step`` is a simulation-only message for lockstep
execution and is not part of the item's interfaces.

Operating modes
---------------

.. list-table:: Modes of the ACC
   :header-rows: 1
   :widths: 18 82

   * - Mode
     - Meaning
   * - ``OFF``
     - Main switch off. No request is issued.
   * - ``STANDBY``
     - Main switch on, not controlling. Activation possible with SET or RESUME within the
       activation speed range.
   * - ``ACTIVE_SPEED``
     - Controlling to the set speed; no relevant vehicle ahead, or speed control demands
       less than gap control.
   * - ``ACTIVE_FOLLOW``
     - Controlling to the time gap behind a relevant vehicle ahead.
   * - ``OVERRIDE``
     - Driver presses the accelerator beyond A-12; ACC issues no request until the pedal
       is released, then returns to the previous active mode.
   * - ``FAULT``
     - Fault reported by ``AccMon``. Activation blocked. If the fault occurs while active
       or in override, a TOR is raised and ``AccMon`` ramps the request to 0. Left only
       when the fault is gone and the driver presses CANCEL.

Transitions are evaluated in a fixed priority order, at most one per 10 ms cycle: main
switch off, fault, brake or CANCEL, speed below 25 km/h, accelerator override, then
speed/follow arbitration (ADR-000 D-11, D-13). The full transition table is part of the
system requirements (M2) and the SysML model (M3).

Operating range and project assumptions
---------------------------------------

These values are project assumptions informed by common ACC practice. They are not taken
from ISO 15622. Changes need an ADR.

.. list-table::
   :header-rows: 1
   :widths: 8 52 40

   * - ID
     - Assumption
     - Value
   * - A-01
     - Activation speed range
     - 30–150 km/h; deactivation with TOR below 25 km/h
   * - A-02
     - Selectable time gaps
     - 1.0 / 1.5 / 2.0 s (default 1.5 s)
   * - A-03
     - Standstill distance in the spacing policy
     - 5 m
   * - A-04
     - Maximum acceleration request
     - +2.0 m/s²
   * - A-05
     - Maximum deceleration request (ACC authority)
     - −3.5 m/s²
   * - A-06
     - Maximum jerk of the request
     - 2.5 m/s³
   * - A-07
     - ACC task period
     - 10 ms
   * - A-08
     - Radar cycle, range, objects
     - 50 ms, 150 m, up to 4 objects
   * - A-09
     - Vehicle dynamics and pedal signal cycle
     - 10 ms
   * - A-10
     - Actuator response
     - First-order lag τ = 0.4 s plus 50 ms dead time
   * - A-11
     - Signal timeout
     - 3 missed cycles of the respective message
   * - A-12
     - Accelerator override threshold
     - Pedal position > 5 %

Above 150 km/h only activation is blocked; an active ACC stays active and decelerates to
the set speed (ADR-000 D-11).

Legal and functional constraints
--------------------------------

- **Driver responsibility.** Level 1 assistance: the driver monitors the traffic, keeps
  hands on the wheel and remains responsible. The ACC never prevents the driver from
  braking or accelerating.
- **Driver precedence.** Brake pedal and CANCEL end active control; the accelerator pedal
  overrides it. The ACC must not issue a positive request while the brake pedal is pressed.
- **Limited authority.** The ACC is a comfort function with bounded authority (A-04 to
  A-06). It is not an emergency braking function; when the needed deceleration exceeds
  A-05, it saturates and raises a TOR.
- **Reference standards (named only).** ISO 15622 describes ACC performance requirements
  and test procedures; this project uses its own assumptions instead of its values.
  ISO 26262 (functional safety) is applied as concepts. ISO 21448 (SOTIF) covers hazards
  from performance limitations of correctly working functions; it is outside this
  project's scope except where named as a known limitation.
- **No type approval.** No regulatory approval or market-specific legal requirement is
  claimed or analysed.

Assumptions on elements outside the ACC ECU
-------------------------------------------

The item relies on elements that are simulated here. **The controllability arguments in
the HARA depend on these assumptions.** They become assumptions of use (``AOU_``) in M2
(ADR-000 D-04, D-15, D-16).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Element
     - Assumption
   * - Cluster (TOR display)
     - Shows the TOR with a latency and visibility that let an attentive driver notice it.
       Raises the TOR on its own and shows ACC as inactive when ``ACC_Cmd`` or
       ``ACC_Status`` times out. Latency values set in M2.
   * - Powertrain and brake actuation
     - Executes the acceleration request within the response of A-10; checks the
       end-to-end protection of ``ACC_Cmd`` on reception. It is **not** assumed to limit
       ACC requests: a wrong request is executed up to about +3 m/s² and −8 m/s² (HARA
       convention, ADR-003).
   * - Brake pedal signal
     - The brake-pedal-pressed signal is correct and timely; a pressed brake pedal is
       never reported as released.
   * - Radar
     - Reported objects are plausible (no ghost object reported as a close target, no
       real moving target missed for longer than the timeout); reports moving objects
       only. A plausible but wrong object defeats both doer and checker, because both read
       the same radar data.

Known limitations
-----------------

- No stop & go: below 25 km/h the ACC deactivates with a TOR; it does not brake to a stop.
- No reaction to stationary objects that were never tracked as moving (the radar model
  reports moving objects only). The driver must brake for them.
- Straight roads only: no curve-based target selection, no lateral control.
- Bounded deceleration (A-05): cannot handle a lead vehicle braking harder than that; it
  saturates and raises a TOR. No emergency braking function exists.
- The checker blocks acceleration for any valid object in a wide lateral band below the
  time-to-collision threshold (ADR-000 D-06). Vehicles in adjacent lanes can therefore
  block acceleration unnecessarily. This is an availability limitation, not a safety one.
- Doer and checker run on one ECU, in one process, sharing hardware, scheduler and memory.
  Freedom from interference is not implemented; this limits any ASIL decomposition
  argument (M2).
