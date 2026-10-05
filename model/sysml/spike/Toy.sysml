// Spike 1 (M0) toy model. Exercises the constructs M3 needs: packages, imports, part defs,
// port defs with directed attributes, a state def and requirement IDs in a satisfy relation.
// Not the SafeCruise architecture; that is written in M3.
package SpikeToy {
    private import ScalarValues::*;

    port def SpeedPort {
        out attribute speed_mps : Real;
    }

    requirement def <'SYS_TOY_001'> ToyRequirement {
        doc /* Toy requirement used only to check that IDs survive parsing. */
    }

    part def Controller {
        in port speedIn : ~SpeedPort;
    }

    part def Sensor {
        out port speedOut : SpeedPort;
    }

    state def ToyModes {
        entry; then Off;
        state Off;
        state On;
        transition off_to_on first Off then On;
        transition on_to_off first On then Off;
    }

    part toySystem {
        part sensor : Sensor;
        part controller : Controller {
            exhibit state modes : ToyModes;
        }
        connect sensor.speedOut to controller.speedIn;
        satisfy requirement toyReq : ToyRequirement by controller;
    }
}
