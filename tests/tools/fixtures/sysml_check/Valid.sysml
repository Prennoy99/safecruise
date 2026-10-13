// Fixture for tests/tools/test_sysml_check.py; not the SafeCruise model.
package CheckFixture {
    part def <'ARC_X_A'> ElementA;
    part def <'ARC_X_B'> ElementB;
    requirement <'SYS_X_1'> systemRequirement;
    requirement <'TSR_X_1'> safetyRequirement;
    part system {
        part a : ElementA;
        part b : ElementB;
    }
    satisfy 'SYS_X_1' by system.a;
    satisfy 'TSR_X_1' by system.a;
    satisfy 'TSR_X_1' by system.b;
}
