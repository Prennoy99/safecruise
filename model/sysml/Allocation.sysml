// Allocation of behaviour and of requirements to the ACC ECU elements. Conventions: ADR-009.
package SafeCruiseAllocation {
    doc /*
     * Mirrors the allocated_to links of the requirements database: for every SYS_ and
     * TSR_ (later SWR_), the parts that satisfy it here are exactly the ARC_ elements it
     * is allocated to there. tools/sysml_check.py enforces this in both directions.
     */
    private import SafeCruiseRequirements::*;

    // Behaviour. Allocated here rather than exhibited or performed inside the part defs, so
    // that the structure views stay within the renderer's element limit (ADR-009).
    state accModes : SafeCruiseModes::AccModes;
    action ecuCycle : SafeCruise::EcuCycle;
    allocate accModes to SafeCruise::safeCruise.accEcu.accCtrl;
    allocate ecuCycle to SafeCruise::safeCruise.accEcu.sched;

    // Requirements

    // Hmi (ARC_HMI)
    satisfy 'SYS_ACC_002' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_003' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_004' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_005' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_006' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_011' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_017' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_019' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_020' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_025' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'SYS_ACC_026' by SafeCruise::safeCruise.accEcu.hmi;
    satisfy 'TSR_ACC_008' by SafeCruise::safeCruise.accEcu.hmi;

    // TgtSel (ARC_TGT_SEL)
    satisfy 'SYS_ACC_027' by SafeCruise::safeCruise.accEcu.tgtSel;

    // AccCtrl (ARC_ACC_CTRL)
    satisfy 'SYS_ACC_001' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_002' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_003' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_004' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_005' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_006' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_007' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_008' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_009' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_010' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_011' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_012' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_013' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_014' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_015' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_016' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_017' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_018' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_021' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_023' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_028' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_029' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_030' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_031' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'SYS_ACC_032' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'TSR_ACC_001' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'TSR_ACC_004' by SafeCruise::safeCruise.accEcu.accCtrl;
    satisfy 'TSR_ACC_008' by SafeCruise::safeCruise.accEcu.accCtrl;

    // AccMon (ARC_ACC_MON)
    satisfy 'SYS_ACC_015' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_016' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_017' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_018' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_022' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_024' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_030' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_033' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'SYS_ACC_037' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_002' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_003' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_005' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_006' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_007' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_009' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_012' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_013' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_014' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_015' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_016' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_017' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_018' by SafeCruise::safeCruise.accEcu.accMon;
    satisfy 'TSR_ACC_019' by SafeCruise::safeCruise.accEcu.accMon;

    // RTE (ARC_RTE)
    satisfy 'TSR_ACC_011' by SafeCruise::safeCruise.accEcu.rte;
    satisfy 'TSR_ACC_022' by SafeCruise::safeCruise.accEcu.rte;

    // COM (ARC_COM)
    satisfy 'SYS_ACC_021' by SafeCruise::safeCruise.accEcu.com;
    satisfy 'SYS_ACC_022' by SafeCruise::safeCruise.accEcu.com;
    satisfy 'SYS_ACC_035' by SafeCruise::safeCruise.accEcu.com;
    satisfy 'SYS_ACC_037' by SafeCruise::safeCruise.accEcu.com;

    // E2E (ARC_E2E)
    satisfy 'SYS_ACC_035' by SafeCruise::safeCruise.accEcu.e2e;
    satisfy 'SYS_ACC_036' by SafeCruise::safeCruise.accEcu.e2e;
    satisfy 'TSR_ACC_010' by SafeCruise::safeCruise.accEcu.e2e;
    satisfy 'TSR_ACC_020' by SafeCruise::safeCruise.accEcu.e2e;
    satisfy 'TSR_ACC_023' by SafeCruise::safeCruise.accEcu.e2e;
    satisfy 'TSR_ACC_024' by SafeCruise::safeCruise.accEcu.e2e;

    // CanIf (ARC_CANIF)
    satisfy 'SYS_ACC_035' by SafeCruise::safeCruise.accEcu.canIf;

    // Scheduler (ARC_SCHED)
    satisfy 'SYS_ACC_034' by SafeCruise::safeCruise.accEcu.sched;
    satisfy 'TSR_ACC_021' by SafeCruise::safeCruise.accEcu.sched;
}
