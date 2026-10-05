Hazard analysis and risk assessment
===================================

:Status: draft. Ratings, reasons and ASILs agreed by pb (ADR-000 D-17); each hazardous
         event stays ``draft`` until pb approves it.
:Applies: ISO 26262-3, clause 6 (hazard analysis and risk assessment), as applied
          concepts only
:Scope: :doc:`decisions/ADR-003-hara-scope`; representation and check:
        :doc:`decisions/ADR-004-hara-representation`

The HARA is done on the item of :doc:`00_item_definition`. Each hazardous event combines
one operational situation with one malfunctioning behaviour of the item. It gets a
severity (S), exposure (E) and controllability (C) class as defined in ISO 26262-3, a
written reason for each class, and the ASIL these give. ``tools/hara_check.py`` checks
that every ASIL follows from its ratings and that nothing is left open (ADR-004).

Conventions
-----------

- **No credit for the item's own safety mechanisms.** Ratings assume the malfunction is
  not caught: no ``AccMon``, no end-to-end check, no authority limits that the item
  itself enforces.
- **Malfunction magnitude.** A malfunctioning request is executed up to the physical
  capability of the actuators: about +3 m/s² (powertrain at motorway speed) and about
  −8 m/s² (full braking, dry road). No limit on the actuator side is credited, because the
  actuators are outside the item and no such limit is specified or verified (ADR-003).
- **Driver.** An attentive Level 1 driver, hands on the wheel and eyes on the road, who
  reacts to an unexpected event in 1.5 s. Where the driver believes the ACC is handling
  the situation (M3), 0.5–1 s more is assumed for complacency.
- **Exposure basis.** Duration of the situation by default, because a random fault occurs
  *during* the situation. Frequency where a latent fault waits for a trigger: all M4
  events (the driver braking) and the cut-in events (OS4). Exposure is rated for the
  situation in all driving; it is not reduced by how often ACC is used or fitted.
- **Severity guide.** In a rear-end collision between two cars, each car's Δv is about
  half the closing speed. Below about 20 km/h Δv per car points to S1, 20–40 km/h to S2;
  high-speed closing, a queue tail or a truck involved points to S3.
- **Road condition.** Wet or low-friction road is not a separate situation; where it
  changes a class, the reason says so (ADR-000 D-05).
- **Persons at risk** are named per hazardous event. Motorway-type roads are assumed, so
  pedestrians and cyclists are not considered.
- **Assumptions.** Controllability reasons may rely on the assumptions on elements outside
  the ACC ECU (TOR display, actuation, brake pedal signal, radar) listed in the item
  definition. A reason that relies on one says which.

Operational situations
----------------------

The speeds are drafting assumptions to make each situation concrete; pb may change them.

.. list-table::
   :header-rows: 1
   :widths: 7 25 15 13 40

   * - ID
     - Situation
     - ACC mode
     - Ego speed
     - Traffic and road
   * - OS1
     - Free motorway driving at high speed
     - ``ACTIVE_SPEED``
     - 100–150 km/h
     - Motorway, dry or wet. No relevant vehicle within radar range in the lane; vehicles
       in adjacent lanes and behind.
   * - OS2
     - Steady following in moderate or dense traffic
     - ``ACTIVE_FOLLOW``
     - 30–130 km/h
     - Lead vehicle at the set time gap (1.0–2.0 s); following vehicles at similar gaps.
   * - OS3
     - Approaching a slower vehicle or the tail of a traffic jam
     - ``ACTIVE_SPEED`` → ``ACTIVE_FOLLOW``
     - 60–150 km/h
     - Slower moving vehicle ahead; closing speed up to the speed difference. A jam tail
       that was never tracked as moving is a known limitation, not part of this
       situation.
   * - OS4
     - Close cut-in
     - ``ACTIVE_SPEED`` or ``ACTIVE_FOLLOW``
     - 60–130 km/h
     - A vehicle from an adjacent lane enters the ego lane at a distance well below the set
       time gap.
   * - OS5
     - Low-speed boundary near 25 km/h
     - ``ACTIVE_FOLLOW``, deactivating below 25 km/h
     - 25–40 km/h
     - Dense, slowing traffic that may come to a stop. The ACC has no stop & go and hands
       back with a TOR below 25 km/h.

Malfunctioning behaviours
-------------------------

Defined at item level, by what reaches the vehicle and the driver, not by cause.

.. list-table::
   :header-rows: 1
   :widths: 7 28 65

   * - ID
     - Malfunction
     - Description
   * - M1
     - Unintended or excessive acceleration
     - Acceleration request when none is needed, or larger than the situation needs,
       including after an unintended activation.
   * - M2
     - Unintended or excessive deceleration
     - Deceleration request when none is needed, or stronger than the situation needs,
       including after an unintended activation.
   * - M3
     - Insufficient or no deceleration, or loss of control, without a takeover request
     - The ACC decelerates less than the situation needs, or stops controlling (request
       withdrawn, mode drops out), and the driver gets no TOR, so the driver may still
       believe the ACC is in control. Includes the cluster showing ACC as active when it is
       not. The worst case is no deceleration at all.
   * - M4
     - Failure to hand back control on brake pedal or CANCEL
     - After the driver brakes or presses CANCEL, the ACC stays active and keeps its
       request.

Coverage
--------

Each cell is either a hazardous event or pruned with a reason in ADR-003.

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * -
     - M1
     - M2
     - M3
     - M4
   * - OS1
     - :need:`HE_OS1_M1`
     - :need:`HE_OS1_M2`
     - pruned (ADR-003)
     - :need:`HE_OS1_M4`
   * - OS2
     - :need:`HE_OS2_M1`
     - :need:`HE_OS2_M2`
     - :need:`HE_OS2_M3`
     - :need:`HE_OS2_M4`
   * - OS3
     - :need:`HE_OS3_M1`
     - :need:`HE_OS3_M2`
     - :need:`HE_OS3_M3`
     - :need:`HE_OS3_M4`
   * - OS4
     - :need:`HE_OS4_M1`
     - :need:`HE_OS4_M2`
     - :need:`HE_OS4_M3`
     - :need:`HE_OS4_M4`
   * - OS5
     - :need:`HE_OS5_M1`
     - :need:`HE_OS5_M2`
     - :need:`HE_OS5_M3`
     - :need:`HE_OS5_M4`

Summary
-------

.. needtable::
   :types: he
   :columns: id as "ID";situation as "OS";malfunction as "M";severity as "S";exposure as "E";controllability as "C";asil as "ASIL";derives_from_back as "Safety goal"
   :sort: id
   :style: table

Hazardous events
----------------

OS1 — Free motorway driving at high speed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. he:: Unintended acceleration at high speed in free driving
   :id: HE_OS1_M1
   :status: approved
   :situation: OS1
   :malfunction: M1
   :severity: S3
   :severity_rationale: Speed keeps rising beyond the set speed; when a slower vehicle or a
      truck comes into view in the lane, the closing speed can exceed 60 km/h, giving more
      than 30 km/h Δv per car or an underride: S3.
   :exposure: E3
   :exposure_rationale: Free high-speed motorway driving with no relevant vehicle ahead is a
      few per cent of all driving time (duration basis): E3.
   :controllability: C1
   :controllability_rationale: +3 m/s² beyond the set speed is felt within about a second
      and seen on the speedometer; with no vehicle ahead, the driver has many seconds to
      brake or cancel before reaching one. More than 99 % of drivers are expected to control
      it: C1.
   :asil: A

   **Hazardous event.** On a free motorway the ACC accelerates beyond the set speed, or
   harder than needed to reach it. Ego speed keeps rising while the driver supervises a
   function that looks normal. Vehicles that come into view ahead, or that change into the
   lane, are approached at a high closing speed.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: Unintended braking at high speed in free driving
   :id: HE_OS1_M2
   :status: approved
   :situation: OS1
   :malfunction: M2
   :severity: S2
   :severity_rationale: From 130 km/h, a follower at a 1 s gap (36 m) reacting after 1.5 s
      and braking at −8 m/s² hits after about 3.8 s at about 43 km/h closing speed, about 22
      km/h Δv per car: S2.
   :exposure: E3
   :exposure_rationale: Free high-speed motorway driving with no relevant vehicle ahead is a
      few per cent of all driving time (duration basis): E3.
   :controllability: C2
   :controllability_rationale: Controllability rests with following drivers. On a free lane
      they are fewer and usually at longer gaps than in dense traffic; most stop in time,
      not all at a 1 s gap: C2.
   :asil: A

   **Hazardous event.** With no vehicle ahead, the ACC brakes without reason or harder than
   needed. Following traffic, which the ACC does not monitor, does not expect the
   deceleration and may run into the ego vehicle.

   **Persons at risk.** Occupants of the ego vehicle and of following vehicles.

.. he:: ACC keeps control after the driver brakes in free driving
   :id: HE_OS1_M4
   :status: approved
   :situation: OS1
   :malfunction: M4
   :severity: S3
   :severity_rationale: The driver brakes at motorway speed, typically for an object the ACC
      does not see. +3 m/s² drive torque leaves a net −5 instead of −8 m/s²: from 130 km/h,
      at the point where full braking would stop (81 m) the car still does about 79 km/h:
      S3.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by braking): drivers
      brake while ACC is active in free motorway driving more than once a month, not on
      almost every drive: E3.
   :controllability: C2
   :controllability_rationale: The driver is already braking and feels less deceleration
      than expected; most press harder or press CANCEL, and the brake can overpower the
      remaining drive torque, but not all compensate in time in an emergency stop: C2.
   :asil: B

   **Hazardous event.** The driver brakes, typically for something the ACC does not see (a
   stationary object, a hazard outside the radar view). The ACC stays active and keeps
   requesting acceleration to hold the set speed, which works against the driver's braking
   and lengthens the stopping distance.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

OS2 — Steady following in moderate or dense traffic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. he:: Unintended acceleration while following
   :id: HE_OS2_M1
   :status: approved
   :situation: OS2
   :malfunction: M1
   :severity: S2
   :severity_rationale: At 100 km/h and a 1.0 s gap (32.8 m including the 5 m offset),
      uncorrected +3 m/s² reaches the lead after about 4.7 s at about 50 km/h closing speed,
      about 25 km/h Δv per car: S2.
   :exposure: E4
   :exposure_rationale: Following another vehicle is more than 10 % of driving time
      (duration basis): E4.
   :controllability: C2
   :controllability_rationale: The acceleration toward the lead is felt and seen; after a
      1.5 s reaction about 3 s remain and moderate braking suffices. A lead braking at the
      same time shortens this. Most, but not 99 %, of drivers control it: C2.
   :asil: B

   **Hazardous event.** While following a vehicle at the set time gap (1.0–2.0 s), the ACC
   accelerates toward it. The gap closes; if the lead vehicle slows at the same time, the
   time left for the driver to react is short.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: Unintended braking while following in dense traffic
   :id: HE_OS2_M2
   :status: approved
   :situation: OS2
   :malfunction: M2
   :severity: S2
   :severity_rationale: Full braking (−8 m/s²) without cause; a follower at a 1 s gap
      reacting after 1.5 s and braking equally hard hits at about 40 km/h closing speed,
      about 20 km/h Δv per car, with a risk of multi-vehicle collisions: S2.
   :exposure: E4
   :exposure_rationale: Following another vehicle is more than 10 % of driving time
      (duration basis): E4.
   :controllability: C3
   :controllability_rationale: Followers in dense traffic often keep gaps below 1 s, shorter
      than a 1.5 s reaction time, and the braking has no visible cause. A substantial share
      of following drivers cannot avoid the collision: C3.
   :asil: C

   **Hazardous event.** While following, the ACC brakes without reason or harder than the
   situation needs. Vehicles behind at similar short gaps may run into the ego vehicle.

   **Persons at risk.** Occupants of the ego vehicle and of following vehicles.

.. he:: Insufficient or no ACC deceleration while following, without TOR
   :id: HE_OS2_M3
   :status: approved
   :situation: OS2
   :malfunction: M3
   :severity: S2
   :severity_rationale: Lead brakes at −3 m/s² from 100 km/h while the ego vehicle coasts
      (about −0.4 m/s²); at a 1.0 s gap, without driver reaction the impact comes after
      about 5 s at about 47 km/h closing speed, about 23 km/h Δv per car: S2.
   :exposure: E4
   :exposure_rationale: Following another vehicle is more than 10 % of driving time
      (duration basis): E4.
   :controllability: C2
   :controllability_rationale: The driver must notice that the ACC does not brake while
      expecting it to; with complacency the reaction takes 2–2.5 s, still inside the about 5
      s available, and brake lights ahead are a strong cue. Most, but not 99 %, of drivers:
      C2.
   :asil: B

   **Hazardous event.** While following, the ACC stops controlling, or brakes less than
   needed, without a takeover request. When the lead vehicle slows, the ego vehicle does
   not slow enough, and the driver, who believes the ACC is still handling it, reacts
   late.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: ACC keeps control after the driver brakes while following
   :id: HE_OS2_M4
   :status: approved
   :situation: OS2
   :malfunction: M4
   :severity: S2
   :severity_rationale: The driver brakes because the lead brakes; drive torque against the
      brakes leaves a net −5 instead of −8 m/s², ending in a rear-end collision at about
      20–40 km/h closing speed, up to about 20 km/h Δv per car: S2.
   :exposure: E4
   :exposure_rationale: Rated by frequency (latent fault, triggered by braking): the driver
      brakes while following with ACC active on almost every ACC drive: E4.
   :controllability: C2
   :controllability_rationale: The driver is already braking and feels less deceleration
      than expected; most press harder or press CANCEL, and the brake can overpower the
      remaining drive torque, but not all compensate in time in an emergency stop: C2.
   :asil: B

   **Hazardous event.** The lead vehicle brakes and the driver brakes too. The ACC stays
   active and keeps a request that works against or limits the driver's braking.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

OS3 — Approaching a slower vehicle or the tail of a traffic jam
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. he:: Unintended acceleration while approaching a slower vehicle
   :id: HE_OS3_M1
   :status: approved
   :situation: OS3
   :malfunction: M1
   :severity: S3
   :severity_rationale: Approaching a slower vehicle or a queue tail at 50–100 km/h speed
      difference, acceleration instead of braking leads to impact at high closing speed;
      trucks are common at queue tails: S3.
   :exposure: E3
   :exposure_rationale: Each approach lasts tens of seconds and happens several times per
      motorway trip; in total 1–10 % of driving time (duration basis): E3.
   :controllability: C2
   :controllability_rationale: The driver sees the slower vehicle and feels the unexpected
      acceleration, but expects the ACC to brake while the distance shrinks fast; most, but
      not 99 %, brake in time: C2.
   :asil: B

   **Hazardous event.** Approaching a slower vehicle or a traffic-jam tail, the ACC
   accelerates instead of starting to decelerate. The closing speed rises and the distance
   left to brake shrinks.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: Excessive braking while approaching a slower vehicle
   :id: HE_OS3_M2
   :status: approved
   :situation: OS3
   :malfunction: M2
   :severity: S2
   :severity_rationale: Full braking (−8 m/s²) without cause; a follower at a 1 s gap
      reacting after 1.5 s and braking equally hard hits at about 40 km/h closing speed,
      about 20 km/h Δv per car, with a risk of multi-vehicle collisions: S2.
   :exposure: E3
   :exposure_rationale: Each approach lasts tens of seconds and happens several times per
      motorway trip; in total 1–10 % of driving time (duration basis): E3.
   :controllability: C2
   :controllability_rationale: Following drivers already see the ego vehicle slowing (brake
      lights, slower traffic ahead) and expect deceleration; fewer are surprised than in
      OS2: C2.
   :asil: A

   **Hazardous event.** Approaching a slower vehicle, the ACC brakes much harder than
   needed. Following traffic expects some deceleration, but not this much, and may run into
   the ego vehicle. Close to OS2 × M2 (ADR-003).

   **Persons at risk.** Occupants of the ego vehicle and of following vehicles.

.. he:: Insufficient or no ACC deceleration while approaching, without TOR
   :id: HE_OS3_M3
   :status: approved
   :situation: OS3
   :malfunction: M3
   :severity: S3
   :severity_rationale: No or too little braking toward a slower vehicle or queue tail at
      50–100 km/h speed difference, with trucks common at queue tails: S3.
   :exposure: E3
   :exposure_rationale: Each approach lasts tens of seconds and happens several times per
      motorway trip; in total 1–10 % of driving time (duration basis): E3.
   :controllability: C2
   :controllability_rationale: The driver expects the ACC to slow down and reacts late
      (complacency), but the approach is visible from up to 150 m and lasts several seconds;
      most, but not 99 %, brake in time: C2.
   :asil: B

   **Hazardous event.** Approaching a slower vehicle or a traffic-jam tail, the ACC stops
   controlling, or brakes less than needed, without a takeover request. The driver, who
   expects the ACC to slow down for the vehicle ahead, notices late. The closing speed can
   be large.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: ACC keeps control after the driver brakes while approaching
   :id: HE_OS3_M4
   :status: approved
   :situation: OS3
   :malfunction: M4
   :severity: S3
   :severity_rationale: Braking toward a queue tail with a net −5 instead of −8 m/s² leaves
      a high residual impact speed: S3.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by braking): braking
      while approaching with ACC active happens more than once a month, not on almost every
      drive: E3.
   :controllability: C2
   :controllability_rationale: The driver is already braking and feels less deceleration
      than expected; most press harder or press CANCEL, and the brake can overpower the
      remaining drive torque, but not all compensate in time in an emergency stop: C2.
   :asil: B

   **Hazardous event.** Approaching a slower vehicle, the driver brakes. The ACC stays
   active and keeps a request that works against or limits the driver's braking.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

OS4 — Close cut-in
~~~~~~~~~~~~~~~~~~

.. he:: Unintended acceleration at a close cut-in
   :id: HE_OS4_M1
   :status: approved
   :situation: OS4
   :malfunction: M1
   :severity: S2
   :severity_rationale: A close cut-in vehicle is typically 10–30 km/h slower; accelerating
      toward it gives impact at up to about 40 km/h closing speed, up to about 20 km/h Δv
      per car: S2.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by the cut-in): close
      cut-ins happen more than once a month in motorway driving, not on almost every drive:
      E3.
   :controllability: C2
   :controllability_rationale: The cut-in is a salient event the driver sees directly, but
      the distance is short and so is the time to brake; most, but not 99 %, avoid the
      collision: C2.
   :asil: A

   **Hazardous event.** A vehicle cuts in at a distance well below the set time gap. Instead
   of opening the gap, the ACC accelerates toward it.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: Excessive braking at a close cut-in
   :id: HE_OS4_M2
   :status: approved
   :situation: OS4
   :malfunction: M2
   :severity: S2
   :severity_rationale: Full braking (−8 m/s²) without cause; a follower at a 1 s gap
      reacting after 1.5 s and braking equally hard hits at about 40 km/h closing speed,
      about 20 km/h Δv per car, with a risk of multi-vehicle collisions: S2.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by the cut-in): close
      cut-ins happen more than once a month in motorway driving, not on almost every drive:
      E3.
   :controllability: C2
   :controllability_rationale: Following drivers see the cut-in too and anticipate some
      braking: C2.
   :asil: A

   **Hazardous event.** A vehicle cuts in and the ACC brakes much harder than needed to
   restore the gap. Following traffic may run into the ego vehicle.

   **Persons at risk.** Occupants of the ego vehicle and of following vehicles.

.. he:: Insufficient or no ACC deceleration at a close cut-in, without TOR
   :id: HE_OS4_M3
   :status: approved
   :situation: OS4
   :malfunction: M3
   :severity: S2
   :severity_rationale: No or too little braking for a cut-in vehicle that is 10–30 km/h
      slower; impact at up to about 30–40 km/h closing speed: S2.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by the cut-in): close
      cut-ins happen more than once a month in motorway driving, not on almost every drive:
      E3.
   :controllability: C1
   :controllability_rationale: The cut-in is directly visible and draws the driver's
      attention; the driver reacts to the cut-in itself rather than waiting for the ACC: C1.
   :asil: QM

   **Hazardous event.** A vehicle cuts in and the ACC stops controlling, or brakes less
   than needed, without a takeover request. It does not open the gap, and the driver, who
   expects the ACC to react, notices late.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: ACC keeps control after the driver brakes at a cut-in
   :id: HE_OS4_M4
   :status: approved
   :situation: OS4
   :malfunction: M4
   :severity: S2
   :severity_rationale: Braking for a cut-in with a net −5 instead of −8 m/s²; residual
      impact at up to about 30–40 km/h closing speed: S2.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by braking for a cut-
      in): more than once a month, not on almost every drive: E3.
   :controllability: C2
   :controllability_rationale: The driver is already braking and feels less deceleration
      than expected; most press harder or press CANCEL, and the brake can overpower the
      remaining drive torque, but not all compensate in time in an emergency stop: C2.
   :asil: A

   **Hazardous event.** The driver brakes in reaction to the cut-in. The ACC stays active
   and keeps a request that works against or limits the driver's braking.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

OS5 — Low-speed boundary near 25 km/h
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. he:: Unintended acceleration in slowing traffic near 25 km/h
   :id: HE_OS5_M1
   :status: approved
   :situation: OS5
   :malfunction: M1
   :severity: S1
   :severity_rationale: At 25–40 km/h, accelerating toward slowing or stopped vehicles gives
      closing speeds below about 40 km/h, below 20 km/h Δv per car: S1.
   :exposure: E3
   :exposure_rationale: Driving at 25–40 km/h in slowing traffic with ACC active is 1–10 %
      of driving time (duration basis): E3.
   :controllability: C2
   :controllability_rationale: Distances are short, but speeds and stopping distances are
      low; most, but not 99 %, of drivers brake in time: C2.
   :asil: QM

   **Hazardous event.** In dense, slowing traffic close to the deactivation speed, the ACC
   accelerates toward vehicles that are slowing down or stopping at short distance.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: Unintended braking in slowing traffic near 25 km/h
   :id: HE_OS5_M2
   :status: approved
   :situation: OS5
   :malfunction: M2
   :severity: S1
   :severity_rationale: Full braking from at most 40 km/h; followers hit at below about 40
      km/h closing speed, below 20 km/h Δv per car: S1.
   :exposure: E3
   :exposure_rationale: Driving at 25–40 km/h in slowing traffic with ACC active is 1–10 %
      of driving time (duration basis): E3.
   :controllability: C2
   :controllability_rationale: Followers in dense slow traffic are close, but expect stops:
      C2.
   :asil: QM

   **Hazardous event.** In dense traffic at low speed, the ACC brakes without reason or
   harder than needed. Following vehicles are close behind.

   **Persons at risk.** Occupants of the ego vehicle and of following vehicles.

.. he:: Deactivation or insufficient deceleration near 25 km/h without TOR
   :id: HE_OS5_M3
   :status: approved
   :situation: OS5
   :malfunction: M3
   :severity: S1
   :severity_rationale: Coasting at about 25 km/h into a stopping queue gives closing speeds
      of 25 km/h or less, about 12 km/h Δv per car: S1.
   :exposure: E3
   :exposure_rationale: Driving at 25–40 km/h in slowing traffic with ACC active is 1–10 %
      of driving time (duration basis): E3. E4, and ASIL A, if daily queue commuting is
      assumed.
   :controllability: C2
   :controllability_rationale: The driver believes the ACC is following and reacts late
      (complacency), but speeds are low and stopping distances short: C2.
   :asil: QM

   **Hazardous event.** Speed falls below 25 km/h and the ACC stops controlling, as
   designed, but without the takeover request; or it drops out, or brakes less than
   needed, without one. The ACC has no stop & go. Traffic ahead slows to a stop while the
   driver believes the ACC is still following.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

.. he:: ACC keeps control after the driver brakes in slowing traffic
   :id: HE_OS5_M4
   :status: approved
   :situation: OS5
   :malfunction: M4
   :severity: S1
   :severity_rationale: Braking at 25–40 km/h with a net −5 instead of −8 m/s²; residual
      impact below about 20 km/h Δv per car: S1.
   :exposure: E3
   :exposure_rationale: Rated by frequency (latent fault, triggered by braking in slowing
      traffic): more than once a month, not on almost every drive: E3.
   :controllability: C2
   :controllability_rationale: The driver is already braking and feels less deceleration
      than expected; most press harder or press CANCEL, and the brake can overpower the
      remaining drive torque, but not all compensate in time in an emergency stop: C2.
   :asil: QM

   **Hazardous event.** In slowing traffic the driver brakes. The ACC stays active and keeps
   a request that works against or limits the driver's braking.

   **Persons at risk.** Occupants of the ego vehicle and of the vehicle ahead.

