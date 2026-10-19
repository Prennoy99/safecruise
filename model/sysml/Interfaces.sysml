// SafeCruise interfaces: CAN messages, message ports and the data the ACC ECU software
// components exchange through the RTE. Conventions: ADR-009.
package SafeCruiseInterfaces {
    doc /*
     * One item def per CAN message (brief §5.6), one attribute per signal, physical units
     * from the ISQ library. Scaling, offsets and ranges of the transmitted integers are set
     * in the DBC in M5; the names here are the design names the DBC and the RTE
     * configuration follow.
     */
    private import ScalarValues::*;
    private import ISQ::*;

    enum def AccMode {
        doc /* Modes of the mode state machine (SafeCruiseModes::AccModes). */
        enum OFF;
        enum STANDBY;
        enum ACTIVE_SPEED;
        enum ACTIVE_FOLLOW;
        enum OVERRIDE;
        enum FAULT;
    }

    // ---------------------------------------------------------------- CAN messages
    abstract item def E2eMessage {
        doc /*
         * End-to-end fields carried by every message (ADR-000 D-15): a 4-bit alive counter
         * and a CRC-8 (SAE J1850 polynomial) over the payload, the alive counter and a
         * per-message data ID. The data ID enters the CRC but is not transmitted.
         */
        attribute aliveCounter : Natural;
        attribute crc : Natural;
    }

    item def RdrObj :> E2eMessage {
        doc /* RDR_Obj1..4: one object of the radar object list. Radar, 50 ms (A-08). */
        attribute range : LengthValue;
        attribute rangeRate : SpeedValue;
        attribute lateralOffset : LengthValue;
        attribute objectId : Natural;
        attribute valid : Boolean;
    }

    item def VehDyn :> E2eMessage {
        doc /* VEH_Dyn: ego motion and pedals. Vehicle, 10 ms (A-09). */
        attribute egoSpeed : SpeedValue;
        attribute egoAccel : AccelerationValue;
        attribute brakePressed : Boolean;
        attribute accelPedalPos : Real {
            doc /* Accelerator pedal position in percent, 0 to 100. */
        }
    }

    item def HmiBtn :> E2eMessage {
        doc /* HMI_Btn: raw button states, true while pressed. HMI panel, 20 ms. */
        attribute mainSwitchOn : Boolean;
        attribute setPressed : Boolean;
        attribute resumePressed : Boolean;
        attribute cancelPressed : Boolean;
        attribute gapPlusPressed : Boolean;
        attribute gapMinusPressed : Boolean;
    }

    item def AccCmd :> E2eMessage {
        doc /* ACC_Cmd: the request to the actuators. ACC ECU, 10 ms; written by AccMon only (ADR-000 D-10). */
        attribute accelRequest : AccelerationValue;
        attribute requestActive : Boolean;
        attribute takeoverRequest : Boolean;
    }

    item def AccStatus :> E2eMessage {
        doc /* ACC_Status: what the cluster shows. ACC ECU, 100 ms. */
        attribute mode : AccMode;
        attribute setSpeed : SpeedValue;
        attribute timeGap : DurationValue;
        attribute targetDetected : Boolean;
    }

    item def CanPdu {
        doc /* One CAN frame as CanIf passes it to COM and back: identifier and payload bytes. */
        attribute canId : Natural;
        attribute payload : Natural[0..8] ordered nonunique;
    }

    // ---------------------------------------------------------------- Message ports
    // The sender owns the port def; receivers use its conjugate (~).
    port def RdrObjPort { out item rdrObj : RdrObj; }
    port def VehDynPort { out item vehDyn : VehDyn; }
    port def HmiBtnPort { out item hmiBtn : HmiBtn; }
    port def AccCmdPort { out item accCmd : AccCmd; }
    port def AccStatusPort { out item accStatus : AccStatus; }

    // ---------------------------------------------------------------- Basic software
    port def PduPort {
        doc /* CanIf to COM: received frames out, frames to send in. */
        out item rxPdu : CanPdu;
        in item txPdu : CanPdu;
    }

    port def E2eServicePort {
        doc /*
         * COM to E2E: COM hands over each received payload for the check and each packed
         * payload for protection; E2E returns the verdict and the protected payload.
         * Includes the round-trip and read-back checks of ADR-007.
         */
        out item checkedPdu : CanPdu;
        in item protectedPdu : CanPdu;
    }

    port def SignalPort {
        doc /* COM to RTE: unpacked received signals as float32 values, and the signals to send (ADR-000 D-12). */
        out item rdrObj : RdrObj[4];
        out item vehDyn : VehDyn;
        out item hmiBtn : HmiBtn;
        in item accCmd : AccCmd;
        in item accStatus : AccStatus;
    }

    attribute def RxStatus {
        doc /* Reception status of one received message (TSR_ACC_011, ADR-000 D-13, D-15). */
        attribute receivedOnce : Boolean;
        attribute ageCycles : Natural {
            doc /* Number of 10 ms cycles since the last valid reception. */
        }
        attribute e2eFault : Boolean {
            doc /* Consecutive end-to-end errors reached N_e2e (TSR_ACC_010). */
        }
    }

    port def RxStatusPort {
        doc /* Status of the six received messages: RDR_Obj1..4, VEH_Dyn, HMI_Btn, in this order. */
        out attribute status : RxStatus[6] ordered;
    }

    // ---------------------------------------------------------------- RTE data between components
    port def RadarObjectsPort {
        doc /* Raw radar object list, as received. AccMon reads it directly (ADR-000 D-06). */
        out item objects : RdrObj[4] ordered;
    }

    port def DriverInputPort {
        doc /* Hmi output: debounced driver inputs and the held settings (SYS_ACC_019, SYS_ACC_020). */
        out attribute mainSwitchOn : Boolean;
        out attribute setEvent : Boolean;
        out attribute resumeEvent : Boolean;
        out attribute cancelEvent : Boolean;
        out attribute setSpeed : SpeedValue;
        out attribute setSpeedStored : Boolean;
        out attribute timeGap : DurationValue;
    }

    port def TargetPort {
        doc /* TgtSel output: the relevant in-lane target (SYS_ACC_027). */
        out attribute targetDetected : Boolean;
        out attribute range : LengthValue;
        out attribute rangeRate : SpeedValue;
    }

    port def ProposalPort {
        doc /* AccCtrl output: the proposed request and the mode. AccMon decides what is sent (ADR-000 D-10). */
        out attribute accelRequest : AccelerationValue;
        out attribute requestActive : Boolean;
        out attribute takeoverRequest : Boolean;
        out attribute mode : AccMode;
    }

    port def ModePort {
        doc /* The mode as written by AccCtrl, read by Hmi in the next cycle. */
        out attribute mode : AccMode;
    }

    port def MonitorFaultPort {
        doc /* AccMon output to AccCtrl: the latched fault, read in the next cycle. */
        out attribute faultLatched : Boolean;
    }

    port def MonitorOutputPort {
        doc /* AccMon output: the content of ACC_Cmd and the mode sent in ACC_Status (TSR_ACC_019, TSR_ACC_022). */
        out attribute accelRequest : AccelerationValue;
        out attribute requestActive : Boolean;
        out attribute takeoverRequest : Boolean;
        out attribute mode : AccMode;
    }
}
