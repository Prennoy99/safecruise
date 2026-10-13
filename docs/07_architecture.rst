Architecture
============

:Status: draft. The ``ARC_`` needs below are the allocation targets of M2; the SysML v2
         model (M3) describes their structure, interfaces, behaviour and allocation.
:Applies: ISO 26262-4, clause 6 (system architectural design), and Automotive SPICE
          SYS.3 / SWE.2, as applied concepts only

Each ``ARC_`` need is one element of the ACC ECU software. Requirements are allocated to
them with ``allocated_to``. Each ``ARC_`` need has a part def of the same name in the SysML
model, with the need's ID as its short name (ADR-009).
Elements outside the ACC ECU (radar, powertrain and brakes, HMI hardware, cluster) are
simulated and are not ``ARC_`` needs; what the item relies on from them is recorded as
assumptions of use in :doc:`04_functional_safety_concept`.

The ASIL of each software component follows from the technical safety requirements
allocated to it and from the decomposition in ADR-006.

Data flow
---------

One 10 ms tick runs the elements in this order (ADR-000 D-14)::

    CanIf ─► COM ─► E2E check ─► RTE ─► Hmi ─► TgtSel ─► AccCtrl ─► AccMon ─► RTE ─► E2E protect ─► COM ─► CanIf
                                                                       ▲
                          raw radar object list, ego speed, pedals ────┘

``AccCtrl`` writes a proposed request; ``AccMon`` is the only element that writes
``ACC_Cmd`` (ADR-000 D-10). ``AccMon`` reads the raw radar object list, not the target
selected by ``TgtSel`` (ADR-000 D-06).

SysML v2 model
--------------

The model lives in ``model/sysml/`` as SysML v2 textual notation and is loaded in this
order:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - File
     - Content
   * - ``Interfaces.sysml``
     - One ``item def`` per CAN message with its signals and units; port defs for the
       messages, for the basic software and for the data the components exchange
       through the RTE.
   * - ``AccModes.sysml``
     - ``state def AccModes``: the six modes and their transitions in the priority order
       of :need:`SYS_ACC_001`.
   * - ``SafeCruise.sysml``
     - Item context, ACC ECU structure, one ``part def`` per ``ARC_`` element, item
       flows, and the order of the runnables in one cycle (``EcuCycle``).
   * - ``Requirements.sysml``
     - One requirement usage per allocated ``SYS_`` and ``TSR_``, identified by its ID
       only. The text stays in this database.
   * - ``Allocation.sysml``
     - The mode machine allocated to ``AccCtrl``, ``EcuCycle`` to the scheduler, and one
       ``satisfy`` per entry in the ``allocated_to`` links of the requirements.

``tools/sysml_check.py`` parses the model with the SysML v2 Pilot Implementation
(ADR-001), reads the parsed model and checks it against ``needs.json``: every ID in the
model exists with the right type; ``ARC_`` needs and part defs match one to one; for every
``SYS_`` and ``TSR_`` the satisfying parts are exactly its ``allocated_to`` elements. CI
runs the check in ``docs-trace-gate`` and renders the views below from the model in the
same step; they are not committed (ADR-009). To render them locally::

    python tools/sysml_check.py build/docs/needs/needs.json --views build/sysml/views

Item context
~~~~~~~~~~~~

The item and its environment, drawn as the logical CAN message flows on one bus. Only the
ACC ECU is implemented; the other elements are simulated, and the item's reliance on them
is recorded as assumptions of use in :doc:`04_functional_safety_concept`.

.. image:: ../build/sysml/views/item_context.svg
   :alt: Interconnection view of the item context
   :width: 100%

ACC ECU structure
~~~~~~~~~~~~~~~~~

CanIf, COM and E2E on the left, the RTE in the middle, the four software components on
the right. A port shown with ``~`` is the receiving (conjugated) side. ``AccMon`` reads
the raw radar objects, pedals and buttons from the RTE, not the outputs of ``TgtSel`` and
``Hmi`` (ADR-000 D-06). Two flows run against the execution order and are read in the next
cycle: the mode from ``AccCtrl`` to ``Hmi`` and the latched fault from ``AccMon`` to
``AccCtrl``.

.. image:: ../build/sysml/views/ecu_structure.svg
   :alt: Interconnection view of the ACC ECU
   :width: 100%

Execution order
~~~~~~~~~~~~~~~

One 10 ms cycle (ADR-000 D-14, :need:`SYS_ACC_034`, :need:`TSR_ACC_021`). The runnable order
is declared again in ``rte/swc_config.yaml`` in M5.

.. image:: ../build/sysml/views/ecu_cycle.svg
   :alt: Action view of one ECU cycle

Mode state machine
~~~~~~~~~~~~~~~~~~

Exhibited by ``AccCtrl``. SysML v2 does not rank transitions whose guards hold at the
same time, so the priority order of :need:`SYS_ACC_001` is written into the guards: each
level is false while a higher level holds, which makes the outgoing guards of every state
mutually exclusive. Activation from STANDBY ranks below level 3. The guards are reviewed
here; the MIL reference (M4) executes the same table.

.. image:: ../build/sysml/views/acc_modes.svg
   :alt: State view of the ACC modes
   :width: 100%

The guards, as written in the model:

.. literalinclude:: ../model/sysml/AccModes.sysml
   :language: text
   :start-after: // Priority levels
   :end-before: // Effects.

Software components
-------------------

.. arc:: Hmi
   :id: ARC_HMI
   :status: draft

   Debounces the buttons (main switch, SET, RESUME, CANCEL, gap +, gap −) and holds the
   set speed and the selected time gap. Runnables ``Hmi_Init``, ``Hmi_Run10ms``.

.. arc:: TgtSel
   :id: ARC_TGT_SEL
   :status: draft

   Selects the relevant in-lane target from the radar object list (lateral offset,
   validity, hysteresis). Doer side of the decomposition (ADR-000 D-06). Runnables
   ``TgtSel_Init``, ``TgtSel_Run10ms``.

.. arc:: AccCtrl
   :id: ARC_ACC_CTRL
   :status: draft

   Doer. Mode state machine and longitudinal control law; writes a proposed acceleration
   request and the mode. Runnables ``AccCtrl_Init``, ``AccCtrl_Run10ms``.

.. arc:: AccMon
   :id: ARC_ACC_MON
   :status: draft

   Checker. Independent limit, plausibility and input-integrity checks; owns
   ``ACC_Cmd``; latches a fault, forces the safe state and raises the takeover request.
   Runnables ``AccMon_Init``, ``AccMon_Run10ms``.

Basic software
--------------

.. arc:: RTE
   :id: ARC_RTE
   :status: draft

   Static port buffers between the components and between components and COM, with a
   new-data flag and an age counter per received message (ADR-000 D-14). Generated from
   ``rte/swc_config.yaml`` (M5).

.. arc:: COM
   :id: ARC_COM
   :status: draft

   Packs and unpacks CAN signals from the DBC and converts between scaled integers and
   float32 (ADR-000 D-12). Generated by cantools (M5). QM under the black-channel argument
   (ADR-007).

.. arc:: E2E
   :id: ARC_E2E
   :status: draft

   End-to-end protection: CRC-8 (SAE J1850 polynomial) over payload, alive counter and a
   per-message data ID, and a 4-bit alive counter; protects ``ACC_Cmd`` and
   ``ACC_Status`` and checks the received messages (ADR-000 D-15). Hand-written.

.. arc:: CanIf
   :id: ARC_CANIF
   :status: draft

   CAN interface with exchangeable backends (``socketcan``, ``udp``; later ``serial``,
   ``stm32_fdcan``). QM under the black-channel argument (ADR-007).

.. arc:: Scheduler
   :id: ARC_SCHED
   :status: draft

   Cyclic scheduler: calls the runnables every 10 ms in the fixed order above (A-07).

Allocation
----------

.. needtable::
   :types: arc
   :columns: id as "ID";title as "Element";allocated_to_back as "Allocated requirements"
   :sort: id
   :style: table
