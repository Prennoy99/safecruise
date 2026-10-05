"""Project-wide pytest hooks.

Test-to-requirement linkage (ADR-000 D-18): a test declares the test-case IDs it
implements with ``@pytest.mark.tc("TC_...")``. Each ID is written to the JUnit XML as
``<property name="tc" value="TC_..."/>`` so that ``tools/trace_check.py`` can link results
to requirements.
"""

import re

import pytest

pytest_plugins = ["pytester"]

TC_ID = re.compile(r"TC_[A-Z0-9]+(?:_[A-Z0-9]+)*")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", 'tc(*ids): test-case IDs this test implements, e.g. tc("TC_SYS_021")'
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        for marker in item.iter_markers(name="tc"):
            if not marker.args:
                raise pytest.UsageError(f"{item.nodeid}: @pytest.mark.tc needs at least one ID")
            for tc_id in marker.args:
                if not isinstance(tc_id, str) or not TC_ID.fullmatch(tc_id):
                    raise pytest.UsageError(f"{item.nodeid}: malformed test-case ID {tc_id!r}")
                item.user_properties.append(("tc", tc_id))
