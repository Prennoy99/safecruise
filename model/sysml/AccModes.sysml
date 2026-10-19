// SafeCruise mode state machine, exhibited by AccCtrl. Conventions: ADR-009.
package SafeCruiseModes {
    doc /*
     * The six modes of brief §5.2 with the transition order of ADR-000 D-11 (SYS_ACC_001):
     * main switch off, fault, brake pedal or CANCEL, speed below 25 km/h, accelerator
     * override, speed/follow arbitration. Activation from STANDBY ranks last.
     *
     * SysML v2 gives no priority among transitions whose guards hold at the same time, so
     * the order is written into the guards: each priority level is one named guard that
     * is false whenever a higher level holds. The guards are therefore mutually exclusive,
     * and at most one transition fires per 10 ms cycle. The Python MIL (M4) and the C code
     * (M5) implement the same table.
     */
    private import ScalarValues::*;
    private import ISQ::*;
    private import SI::*;
    private import SafeCruiseInterfaces::AccMode;

    state def AccModes {
        // Inputs, as AccCtrl reads them in one cycle.
        in attribute mainSwitchOn : Boolean;
        in attribute monitorFault : Boolean;  // latched by AccMon, read in the next cycle (D-14)
        in attribute brakePressed : Boolean;
        in attribute cancelEvent : Boolean;
        in attribute setEvent : Boolean;
        in attribute resumeEvent : Boolean;
        in attribute setSpeedStored : Boolean;
        in attribute allInputsReceived : Boolean;  // every message received at least once (D-13)
        in attribute egoSpeed : SpeedValue;
        in attribute accelPedalPos : Real;  // percent
        // A relevant target is selected and the gap control demands less than the speed
        // control (SYS_ACC_008).
        in attribute followDemanded : Boolean;

        // Design values from the project assumptions.
        attribute vActivateMin : SpeedValue = 30 [km/h];   // A-01
        attribute vActivateMax : SpeedValue = 150 [km/h];  // A-01
        attribute vDeactivate : SpeedValue = 25 [km/h];    // A-01
        attribute pedalOverride : Real = 5.0;              // A-12, percent

        // The mode left on entry to OVERRIDE, to return to (SYS_ACC_010).
        attribute leftMode : AccMode;

        // Priority levels (SYS_ACC_001). Each is false while a higher one holds.
        attribute lvl1MainOff : Boolean = not mainSwitchOn;
        attribute lvl2Fault : Boolean = mainSwitchOn and monitorFault;
        attribute lvl3BrakeOrCancel : Boolean =
            mainSwitchOn and not monitorFault and (brakePressed or cancelEvent);
        attribute belowLvl3 : Boolean =
            mainSwitchOn and not monitorFault and not brakePressed and not cancelEvent;
        attribute lvl4LowSpeed : Boolean = belowLvl3 and egoSpeed < vDeactivate;
        attribute lvl5Override : Boolean =
            belowLvl3 and egoSpeed >= vDeactivate and accelPedalPos > pedalOverride;
        attribute lvl5ReleaseLow : Boolean =
            belowLvl3 and accelPedalPos <= pedalOverride and egoSpeed < vDeactivate;
        attribute lvl5ReleaseToSpeed : Boolean =
            belowLvl3 and accelPedalPos <= pedalOverride and egoSpeed >= vDeactivate
            and leftMode == AccMode::ACTIVE_SPEED;
        attribute lvl5ReleaseToFollow : Boolean =
            belowLvl3 and accelPedalPos <= pedalOverride and egoSpeed >= vDeactivate
            and leftMode == AccMode::ACTIVE_FOLLOW;
        attribute lvl6Follow : Boolean =
            belowLvl3 and egoSpeed >= vDeactivate and accelPedalPos <= pedalOverride
            and followDemanded;
        attribute lvl6Speed : Boolean =
            belowLvl3 and egoSpeed >= vDeactivate and accelPedalPos <= pedalOverride
            and not followDemanded;
        attribute activation : Boolean =
            belowLvl3 and allInputsReceived
            and egoSpeed >= vActivateMin and egoSpeed <= vActivateMax
            and (setEvent or (resumeEvent and setSpeedStored));
        // Leaving FAULT (SYS_ACC_017): AccMon releases its latch only in a cycle in which it
        // reads CANCEL and no fault condition holds (TSR_ACC_016). AccCtrl runs before AccMon
        // and sees the release one cycle later, when the CANCEL event is gone, so it follows
        // the release itself rather than a second CANCEL (ADR-009).
        attribute faultReleased : Boolean = mainSwitchOn and not monitorFault;

        // Effects. The request ramps and flags are AccMon's (ADR-000 D-10); AccCtrl only
        // proposes them.
        action raiseTor;       // propose the TOR (SYS_ACC_013, SYS_ACC_014, SYS_ACC_015)
        action storeLeftMode;  // remember ACTIVE_SPEED or ACTIVE_FOLLOW for SYS_ACC_010

        entry; then OFF;  // SYS_ACC_018

        state OFF;
        state STANDBY;
        state ACTIVE_SPEED;
        state ACTIVE_FOLLOW;
        state OVERRIDE;
        state FAULT;

        // Level 1: main switch off (SYS_ACC_003)
        transition standby_off first STANDBY if lvl1MainOff then OFF;
        transition speed_off first ACTIVE_SPEED if lvl1MainOff then OFF;
        transition follow_off first ACTIVE_FOLLOW if lvl1MainOff then OFF;
        transition override_off first OVERRIDE if lvl1MainOff then OFF;
        transition fault_off first FAULT if lvl1MainOff then OFF;

        // Level 2: monitor fault (SYS_ACC_015, SYS_ACC_016)
        transition standby_fault first STANDBY if lvl2Fault then FAULT;
        transition speed_fault first ACTIVE_SPEED if lvl2Fault do raiseTor then FAULT;
        transition follow_fault first ACTIVE_FOLLOW if lvl2Fault do raiseTor then FAULT;
        transition override_fault first OVERRIDE if lvl2Fault do raiseTor then FAULT;

        // Level 3: brake pedal or CANCEL (SYS_ACC_011); leaving FAULT (SYS_ACC_017)
        transition speed_standby first ACTIVE_SPEED if lvl3BrakeOrCancel then STANDBY;
        transition follow_standby first ACTIVE_FOLLOW if lvl3BrakeOrCancel then STANDBY;
        transition override_standby first OVERRIDE if lvl3BrakeOrCancel then STANDBY;
        transition fault_standby first FAULT if faultReleased then STANDBY;

        // Level 4: speed below 25 km/h (SYS_ACC_013)
        transition speed_low first ACTIVE_SPEED if lvl4LowSpeed do raiseTor then STANDBY;
        transition follow_low first ACTIVE_FOLLOW if lvl4LowSpeed do raiseTor then STANDBY;

        // Level 5: accelerator override and its end (SYS_ACC_009, SYS_ACC_010, SYS_ACC_014)
        transition speed_override first ACTIVE_SPEED if lvl5Override do storeLeftMode then OVERRIDE;
        transition follow_override first ACTIVE_FOLLOW if lvl5Override do storeLeftMode then OVERRIDE;
        transition override_low first OVERRIDE if lvl5ReleaseLow do raiseTor then STANDBY;
        transition override_speed first OVERRIDE if lvl5ReleaseToSpeed then ACTIVE_SPEED;
        transition override_follow first OVERRIDE if lvl5ReleaseToFollow then ACTIVE_FOLLOW;

        // Level 6: speed/follow arbitration (SYS_ACC_008, SYS_ACC_029)
        transition speed_follow first ACTIVE_SPEED if lvl6Follow then ACTIVE_FOLLOW;
        transition follow_speed first ACTIVE_FOLLOW if lvl6Speed then ACTIVE_SPEED;

        // Main switch on (SYS_ACC_002) and activation (SYS_ACC_004 to SYS_ACC_007)
        transition off_standby first OFF if mainSwitchOn then STANDBY;
        transition standby_active first STANDBY if activation then ACTIVE_SPEED;
    }
}
