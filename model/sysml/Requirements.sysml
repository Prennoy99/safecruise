// Requirement stubs by ID, for the satisfy relations in Allocation.sysml. Conventions: ADR-009.
package SafeCruiseRequirements {
    doc /*
     * One requirement usage per allocated requirement, identified by its ID (short name).
     * The text, ASIL, status and links live in the requirements database (docs/,
     * sphinx-needs) and nowhere else; tools/sysml_check.py checks every ID against it.
     */

    // System requirements (docs/03)
    requirement <'SYS_ACC_001'> transitionPriority;
    requirement <'SYS_ACC_002'> mainSwitchOn;
    requirement <'SYS_ACC_003'> mainSwitchOff;
    requirement <'SYS_ACC_004'> activationWithSet;
    requirement <'SYS_ACC_005'> activationWithResume;
    requirement <'SYS_ACC_006'> resumeWithoutStoredSetSpeed;
    requirement <'SYS_ACC_007'> activationBlockedOutsideTheSpeedRange;
    requirement <'SYS_ACC_008'> speedAndFollowArbitration;
    requirement <'SYS_ACC_009'> acceleratorOverride;
    requirement <'SYS_ACC_010'> endOfOverride;
    requirement <'SYS_ACC_011'> brakePedalOrCancelEndsActiveControl;
    requirement <'SYS_ACC_012'> highSpeedWhileActive;
    requirement <'SYS_ACC_013'> deactivationBelow25kmh;
    requirement <'SYS_ACC_014'> overrideReleasedBelow25kmh;
    requirement <'SYS_ACC_015'> faultWhileActive;
    requirement <'SYS_ACC_016'> faultWhileNotActive;
    requirement <'SYS_ACC_017'> leavingFault;
    requirement <'SYS_ACC_018'> startup;
    requirement <'SYS_ACC_019'> buttonDebouncing;
    requirement <'SYS_ACC_020'> timeGapSelection;
    requirement <'SYS_ACC_021'> modeDisplay;
    requirement <'SYS_ACC_022'> takeoverRequestSignal;
    requirement <'SYS_ACC_023'> speedControlAccuracy;
    requirement <'SYS_ACC_024'> requestRampAtLowSpeedDeactivation;
    requirement <'SYS_ACC_025'> setSpeedAdjustment;
    requirement <'SYS_ACC_026'> setSpeedIncrease;
    requirement <'SYS_ACC_027'> targetSelection;
    requirement <'SYS_ACC_028'> gapControl;
    requirement <'SYS_ACC_029'> returnToSetSpeed;
    requirement <'SYS_ACC_030'> accelerationRequestLimits;
    requirement <'SYS_ACC_031'> jerkLimit;
    requirement <'SYS_ACC_032'> torAtTheDecelerationLimit;
    requirement <'SYS_ACC_033'> noRequestOutsideActiveModes;
    requirement <'SYS_ACC_034'> cyclicExecution;
    requirement <'SYS_ACC_035'> commandMessage;
    requirement <'SYS_ACC_036'> inputEndToEndCheck;
    requirement <'SYS_ACC_037'> inputTimeout;

    // Technical safety requirements (docs/05)
    requirement <'TSR_ACC_001'> controllerOutputLimits;
    requirement <'TSR_ACC_002'> monitorLimitAndJerkCheck;
    requirement <'TSR_ACC_903'> monitorAccelerationBlock;
    requirement <'TSR_ACC_004'> controllerAccelerationBlock;
    requirement <'TSR_ACC_005'> positiveRequestAgainstTheBlock;
    requirement <'TSR_ACC_006'> monitorActivationRecord;
    requirement <'TSR_ACC_007'> monitorBrakePedalAndCancel;
    requirement <'TSR_ACC_008'> controllerBrakePedalAndCancel;
    requirement <'TSR_ACC_009'> monitorAcceleratorPedal;
    requirement <'TSR_ACC_010'> endToEndCheckOfReceivedMessages;
    requirement <'TSR_ACC_011'> messageAge;
    requirement <'TSR_ACC_012'> monitorInputFaults;
    requirement <'TSR_ACC_013'> monitorPlausibilityChecks;
    requirement <'TSR_ACC_014'> requestedAgainstMeasuredDeceleration;
    requirement <'TSR_ACC_015'> monitorTakeoverRequestAtShortTimeToCollision;
    requirement <'TSR_ACC_016'> faultLatchAndRelease;
    requirement <'TSR_ACC_017'> positiveRequestAtAFault;
    requirement <'TSR_ACC_018'> negativeRequestAtAFault;
    requirement <'TSR_ACC_019'> takeoverRequestAndModeAtAFault;
    requirement <'TSR_ACC_020'> endToEndProtectionOfTheOutputs;
    requirement <'TSR_ACC_021'> cyclicExecutionOfTheMonitor;
    requirement <'TSR_ACC_022'> monitorOutputsThroughTheRte;
    requirement <'TSR_ACC_023'> readBackOfThePackedCommand;
    requirement <'TSR_ACC_024'> roundTripCheckOfReceivedMessages;
}
