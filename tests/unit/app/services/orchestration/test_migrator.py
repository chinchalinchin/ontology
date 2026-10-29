"""
@domain.test
@test.unit
@app.services
@workflow.injection
@workflow.hydration

# Ontology: tests.unit.app.services.orchestration.test_migrator
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import AssetInstances

# ------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_hydration,
    pytest.mark.workflow_injection,
]

# ------------------------------------------------------------------


def test_migrator_no_target(mock_migrator):
    assert mock_migrator.step(budget_ms=16) is True


def test_migrator_time_slicing(mock_migrator, testbed, monkeypatch):
    mock_migrator.board.clear()
    mock_migrator.target = testbed

    # Step 1: exceed budget after first task (start=0.0, check1=0.001 -> runs 1 task, check2=1.0 -> 1000ms > 16ms)
    times_step_1 = iter([0.0, 0.001, 1.0])
    monkeypatch.setattr(
        "app.services.orchestration.migrator.time.perf_counter",
        lambda: next(times_step_1, 1.0),
    )
    assert mock_migrator.step(budget_ms=16) is False
    assert mock_migrator.target == testbed
    assert mock_migrator._generator is not None
    assert mock_migrator.current == 1

    # Step 2: complete remaining tasks within budget
    monkeypatch.setattr(
        "app.services.orchestration.migrator.time.perf_counter",
        lambda: 0.0,
    )
    assert mock_migrator.step(budget_ms=16) is True
    assert mock_migrator.target is None
    assert mock_migrator._generator is None
    assert mock_migrator.current == mock_migrator.maximum


@pytest.mark.workflow_compositions
def test_migrator_build_generator_compositions(mock_migrator, testbed):
    mock_migrator.board.clear()
    mock_migrator.target = testbed

    for _ in mock_migrator._build_generator():
        pass

    struts = mock_migrator.board.instances(AssetInstances.STRUTS.value, "0")
    doors = mock_migrator.board.instances(AssetInstances.DOORS.value, "0")
    assert len(struts) > 0
    assert len(doors) > 0


@pytest.mark.category_crafts
def test_migrator_build_generator_bridges(mock_migrator, testbed):
    """
    Verify Migrator expands CraftState bridge instances in the testbed via Decomposer
    into constituent unit assets on the board.
    """
    mock_migrator.board.clear()
    mock_migrator.target = testbed

    for _ in mock_migrator._build_generator():
        pass

    bridges = mock_migrator.board.bridges("0")
    assert len(bridges) == 6
    assert any(b.name == "test-horizontal-bridge-0" for b in bridges)
    assert any(b.name == "test-horizontal-bridge-1" for b in bridges)
    assert any(b.name == "test-verical-bridge-0" for b in bridges)


def test_migrator_build_generator_assets(mock_migrator, testbed):
    mock_migrator.board.clear()
    mock_migrator.target = testbed

    for _ in mock_migrator._build_generator():
        pass

    assert len(mock_migrator.board.assets()) > 0
    assert mock_migrator.current == mock_migrator.maximum
    assert mock_migrator.board.player() is not None
    assert len(mock_migrator.board.perimeters.get("0", [])) > 0