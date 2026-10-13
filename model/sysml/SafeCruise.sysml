// SafeCruise item context and ACC ECU structure. Conventions: ADR-009.
package SafeCruise {
    doc /*
     * The item is the vehicle-level ACC function (brief §4.1). Only the ACC ECU software is
     * implemented; the radar, the vehicle signals, the HMI panel, the cluster and the
     * actuators are simulated, and what the item relies on from them is recorded as
     * assumptions of use (AOU_ACC_001 to AOU_ACC_010).
     *
     * Each element of the ACC ECU software is a part def whose short name is the ID of its
     * ARC_ need in the requirements database. tools/sysml_check.py checks the two against
     * each other.
     */
    private import ScalarValues::*;
    private import SafeCruiseInterfaces::*;

    // ---------------------------------------------------------------- Simulated elements
    part def Radar {
        doc /* Front radar, 50 ms cycle, up to 4 moving objects (A-08; AOU_ACC_008 to AOU_ACC_010). */
        out port rdrObj : RdrObjPort[4];
    }
    part def VehicleSensors {
        doc /* Ego speed, ego acceleration and pedal signals (A-09; AOU_ACC_006, AOU_ACC_007). */
        out port vehDyn : VehDynPort;
    }
    part def HmiPanel {
        doc /* Steering-wheel buttons and the main switch. */
        out port hmiBtn : HmiBtnPort;
    }
    part def Cluster {
        doc /* Shows the mode and the takeover request (AOU_ACC_001, AOU_ACC_002). */
        in port accCmd : ~AccCmdPort;
        in port accStatus : ~AccStatusPort;
    }
    part def Actuators {
        doc /* Powertrain and brakes; execute ACC_Cmd after its receiver check (A-10; AOU_ACC_003 to AOU_ACC_005). */
        in port accCmd : ~AccCmdPort;
    }

    // ---------------------------------------------------------------- ACC ECU software
    part def <'ARC_HMI'> Hmi {
        doc /* Debounces the buttons; holds set speed and time gap. QM. */
        in port hmiBtn : ~HmiBtnPort;
        in port vehDyn : ~VehDynPort;
        in port mode : ~ModePort;
        out port driverInput : DriverInputPort;
    }
    part def <'ARC_TGT_SEL'> TgtSel {
        doc /* Selects the relevant in-lane target. Doer side (ADR-000 D-06, ADR-006). */
        in port radarObjects : ~RadarObjectsPort;
        out port target : TargetPort;
    }
    part def <'ARC_ACC_CTRL'> AccCtrl {
        doc /* Doer: mode state machine and control law; proposes the request. */
        in port driverInput : ~DriverInputPort;
        in port target : ~TargetPort;
        in port vehDyn : ~VehDynPort;
        in port rxStatus : ~RxStatusPort;
        in port monitorFault : ~MonitorFaultPort;
        out port proposal : ProposalPort;
        out port mode : ModePort;
    }
    part def <'ARC_ACC_MON'> AccMon {
        doc /*
         * Checker: limit, plausibility and input checks on the raw inputs; the only writer
         * of ACC_Cmd (ADR-000 D-10); latches a fault and reaches the safe state on its own.
         */
        in port proposal : ~ProposalPort;
        in port radarObjects : ~RadarObjectsPort;
        in port vehDyn : ~VehDynPort;
        in port hmiBtn : ~HmiBtnPort;
        in port rxStatus : ~RxStatusPort;
        out port output : MonitorOutputPort;
        out port monitorFault : MonitorFaultPort;
    }
    part def <'ARC_RTE'> RTE {
        doc /* Static port buffers with same-cycle propagation; received-once flag and age per message (ADR-000 D-14). */
        in port signals : ~SignalPort;
        in port rxStatus : ~RxStatusPort;
        out port radarObjects : RadarObjectsPort;
        out port vehDyn : VehDynPort;
        out port hmiBtn : HmiBtnPort;
        out port rxStatusOut : RxStatusPort;
        in port monitorOutput : ~MonitorOutputPort;
        in port driverInput : ~DriverInputPort;
        in port target : ~TargetPort;
    }
    part def <'ARC_COM'> COM {
        doc /* Packs and unpacks the signals of the DBC; scaled integers to float32. QM, black channel (ADR-007). */
        port pdu : ~PduPort;
        port e2e : E2eServicePort;
        out port signals : SignalPort;
    }
    part def <'ARC_E2E'> E2E {
        doc /* CRC-8 and alive counter: checks received messages, protects ACC_Cmd and ACC_Status (ADR-000 D-15, ADR-007). */
        port e2e : ~E2eServicePort;
        out port rxStatus : RxStatusPort;
    }
    part def <'ARC_CANIF'> CanIf {
        doc /* CAN interface with exchangeable backends (socketcan, udp). QM, black channel (ADR-007). */
        in port rdrObj : ~RdrObjPort[4];
        in port vehDyn : ~VehDynPort;
        in port hmiBtn : ~HmiBtnPort;
        out port accCmd : AccCmdPort;
        out port accStatus : AccStatusPort;
        port pdu : PduPort;
    }
    part def <'ARC_SCHED'> Scheduler {
        doc /* Calls the runnables every 10 ms (A-07) in the order of EcuCycle. */
    }

    action def EcuCycle {
        doc /* One 10 ms cycle, fixed order (ADR-000 D-14, SYS_ACC_034, TSR_ACC_021). */
        first start;
        then action comReceive { doc /* COM receive and E2E check. */ }
        then action hmiRun { doc /* Hmi_Run10ms */ }
        then action tgtSelRun { doc /* TgtSel_Run10ms */ }
        then action accCtrlRun { doc /* AccCtrl_Run10ms */ }
        then action accMonRun { doc /* AccMon_Run10ms */ }
        then action comTransmit { doc /* E2E protection and COM transmit. */ }
        then done;
    }

    part def AccEcu {
        doc /*
         * Flows between components are realised by the RTE as static buffers. A flow drawn
         * from a component that runs later in EcuCycle is read in the next cycle.
         */
        in port rdrObj : ~RdrObjPort[4];
        in port vehDyn : ~VehDynPort;
        in port hmiBtn : ~HmiBtnPort;
        out port accCmd : AccCmdPort;
        out port accStatus : AccStatusPort;

        part canIf : CanIf;
        part com : COM;
        part e2e : E2E;
        part rte : RTE;
        part sched : Scheduler;
        part hmi : Hmi;
        part tgtSel : TgtSel;
        part accCtrl : AccCtrl;
        part accMon : AccMon;

        // ECU boundary to CanIf
        bind rdrObj = canIf.rdrObj;
        bind vehDyn = canIf.vehDyn;
        bind hmiBtn = canIf.hmiBtn;
        bind accCmd = canIf.accCmd;
        bind accStatus = canIf.accStatus;

        // Basic software
        connect canIf.pdu to com.pdu;
        connect com.e2e to e2e.e2e;
        connect com.signals to rte.signals;
        flow from e2e.rxStatus to rte.rxStatus;

        // RTE to components
        flow from rte.radarObjects to tgtSel.radarObjects;
        flow from rte.radarObjects to accMon.radarObjects;
        flow from rte.hmiBtn to hmi.hmiBtn;
        flow from rte.hmiBtn to accMon.hmiBtn;
        flow from rte.vehDyn to hmi.vehDyn;
        flow from rte.vehDyn to accCtrl.vehDyn;
        flow from rte.vehDyn to accMon.vehDyn;
        flow from rte.rxStatusOut to accCtrl.rxStatus;
        flow from rte.rxStatusOut to accMon.rxStatus;

        // Between components
        flow from hmi.driverInput to accCtrl.driverInput;
        flow from tgtSel.target to accCtrl.target;
        flow from accCtrl.proposal to accMon.proposal;
        flow from accCtrl.mode to hmi.mode;                 // next cycle
        flow from accMon.monitorFault to accCtrl.monitorFault;  // next cycle

        // Components to RTE (ACC_Cmd and ACC_Status content)
        flow from accMon.output to rte.monitorOutput;
        flow from hmi.driverInput to rte.driverInput;
        flow from tgtSel.target to rte.target;
    }

    part def SafeCruiseItem {
        doc /* The item and its environment: one CAN bus, drawn as the logical message flows. */
        part radar : Radar;
        part vehicle : VehicleSensors;
        part hmiPanel : HmiPanel;
        part cluster : Cluster;
        part actuators : Actuators;
        part accEcu : AccEcu;

        flow from radar.rdrObj to accEcu.rdrObj;
        flow from vehicle.vehDyn to accEcu.vehDyn;
        flow from hmiPanel.hmiBtn to accEcu.hmiBtn;
        flow from accEcu.accCmd to actuators.accCmd;
        flow from accEcu.accCmd to cluster.accCmd;
        flow from accEcu.accStatus to cluster.accStatus;
    }

    part safeCruise : SafeCruiseItem;
}
