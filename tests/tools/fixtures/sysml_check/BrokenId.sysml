// Deliberately broken fixture: SYS_X_9 does not exist in the needs of the test.
package CheckFixture {
    part def <'ARC_X_A'> ElementA;
    part def <'ARC_X_B'> ElementB;
    requirement <'SYS_X_9'> systemRequirement;
    requirement <'TSR_X_1'> safetyRequirement;
    part system {
        part a : ElementA;
        part b : ElementB;
    }
    satisfy 'SYS_X_9' by system.a;
    satisfy 'TSR_X_1' by system.a;
    satisfy 'TSR_X_1' by system.b;
}
