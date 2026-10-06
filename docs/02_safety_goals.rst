Safety goals
============

:Status: draft. Wording, ASIL, safe state and FTTI agreed by pb (ADR-000 D-17); each
         goal stays ``draft`` until pb approves it.
:Applies: ISO 26262-3, clause 6 (safety goals), as applied concepts only

One safety goal per malfunctioning behaviour of the HARA (:doc:`01_hara`). Each goal
derives from the hazardous events it covers; its ASIL is the highest ASIL among them,
which ``tools/hara_check.py`` checks (ADR-004). If pb rates every event of a goal as QM,
pb decides whether the goal is kept.

Safe state
----------

The initial proposal was one safe state for all goals: ACC deactivated, takeover request
active, acceleration request ramped to 0 m/s² at bounded jerk, then no request issued.
Each goal sets its own safe state, because one ramp does not fit all four:

- a ramp limited by the comfort jerk (A-06) can take longer than the FTTI allows;
- removing a deceleration at once can itself be hazardous when braking is needed;
- when the item has lost control (``SG_ACC_003``), it cannot be relied on to reach the
  safe state itself, so the safe state relies on the cluster raising the TOR on a
  message timeout (assumption in :doc:`00_item_definition`).

Fault tolerant time interval
----------------------------

The FTTI written here is an initial value. The MIL experiment in M4 measures, for an
injected worst-case unintended acceleration, the time from fault onset to a hazard
criterion that pb defines beforehand; the safety goals are revised after it if needed,
with an ADR.

Goals
-----

.. sg:: Avoid unintended or excessive acceleration caused by the ACC
   :id: SG_ACC_001
   :status: approved
   :derives_from: HE_OS1_M1, HE_OS2_M1, HE_OS3_M1, HE_OS4_M1, HE_OS5_M1
   :asil: B
   :safe_state: ACC deactivated and takeover request active; positive acceleration
      request cut to 0 m/s² at once, not limited by the comfort jerk A-06; then no request
      issued.
   :ftti_ms: 1000

   Covers malfunction M1, including acceleration after an unintended activation.

   **FTTI basis.** At 100 km/h and a 1.0 s gap, +3 m/s² brings the time headway below
   0.5 s after about 3 s. 1000 ms leaves margin for detection and the actuator response
   (A-10). Cutting a positive request at once is harmless, like releasing the throttle.

.. sg:: Avoid unintended or excessive deceleration caused by the ACC
   :id: SG_ACC_002
   :status: approved
   :derives_from: HE_OS1_M2, HE_OS2_M2, HE_OS3_M2, HE_OS4_M2, HE_OS5_M2
   :asil: C
   :safe_state: ACC deactivated and takeover request active; deceleration request
      limited to A-05 (−3.5 m/s²) at once, then ramped to 0 m/s² at the jerk limit A-06;
      then no request issued.
   :ftti_ms: 500

   Covers malfunction M2, including deceleration after an unintended activation.

   **FTTI basis.** Through the actuator lag (A-10), a −8 m/s² request reaches only about
   −5 m/s² after 500 ms, so little speed is lost before followers react (1.5 s). The
   ramp from A-05 to 0 takes about 1.4 s and gives the driver time to take over braking
   that is still needed.

.. sg:: Avoid insufficient or lost ACC deceleration without informing the driver
   :id: SG_ACC_003
   :status: approved
   :derives_from: HE_OS2_M3, HE_OS3_M3, HE_OS4_M3, HE_OS5_M3
   :asil: B
   :safe_state: Driver informed: takeover request active and ACC shown as inactive, by
      the cluster on a message timeout if the ACC ECU cannot do it; no positive
      acceleration request.
   :ftti_ms: 1000

   Covers malfunction M3: too little deceleration, lost control or a wrong mode display,
   each without a takeover request (ADR-003).

   **FTTI basis.** With the lead braking at −3 m/s² at a 1.0 s gap and the ego vehicle
   coasting, the impact comes after about 5 s; a TOR within 1000 ms leaves the driver
   enough of that time to react, including the complacency allowance.

.. sg:: Release longitudinal control to the driver on brake pedal or CANCEL
   :id: SG_ACC_004
   :status: approved
   :derives_from: HE_OS1_M4, HE_OS2_M4, HE_OS3_M4, HE_OS4_M4, HE_OS5_M4
   :asil: B
   :safe_state: ACC not active (STANDBY) and no acceleration request issued while the
      brake pedal is pressed or after CANCEL.
   :ftti_ms: 500

   Covers malfunction M4.

   **FTTI basis.** Drive torque during driver braking costs stopping distance from the
   first moment; +3 m/s² for 500 ms against full braking costs about 1.5 m/s of speed
   reduction, which a driver who is already braking can still make up.

Summary
-------

.. needtable::
   :types: sg
   :columns: id as "ID";title as "Safety goal";asil as "ASIL";safe_state as "Safe state";ftti_ms as "FTTI [ms]";derives_from as "Hazardous events"
   :sort: id
   :style: table
