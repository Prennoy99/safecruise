/**
 * @file test_hmi_scaffold.c
 * @brief M0 wiring check: Unity, CTest and the Hmi SWC link and run.
 *
 * Not a requirements-based test; it verifies no TC_. Requirement tests are named
 * test_TC_<...> (ADR-000 D-18) and arrive with the SWR_s in M5.
 */
#include "unity.h"
#include "Hmi.h"

void setUp(void)
{
}

void tearDown(void)
{
}

static void test_scaffold_runnables_link_and_return(void)
{
    Hmi_Init();
    Hmi_Run10ms();
    TEST_PASS();
}

int main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_scaffold_runnables_link_and_return);
    return UNITY_END();
}
