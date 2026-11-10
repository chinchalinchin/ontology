"""
@domain.test
@test.unit
@app.service
@workflow.injection
@workflow.hydration

# Ontology: Tests - tests.unit.app.services.orchestration.test_migrator

Unit tests verifying Migrator time-sliced generator execution, composition
unpacking, multiplied asset expansion, door shadow projection, player property
binding, and post-hydration perimeter and fluid initialization.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.state import DoorState, StateSchema
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    LayerProjections,
    Seasons,
)

# Cython Libraries
from libs.core.models import Position

# ------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
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
    interior_struts = mock_migrator.board.instances(
        AssetInstances.STRUTS.value, "house-layer-2"
    )
    interior_doors = mock_migrator.board.instances(
        AssetInstances.DOORS.value, "house-layer-2"
    )
    assert len(struts) > 0
    assert len(doors) > 0
    assert len(interior_struts) > 0
    assert len(interior_doors) == 1


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


@pytest.mark.category_objects
def test_migrator_build_generator_standalone_doors(
    mock_migrator,
    mock_state_schema: StateSchema,
    testbed: str,
    monkeypatch,
):
    """
    Verifies Migrator routes standalone DoorState tasks through Decomposer.project(),
    instantiating both the primary IN door and its reciprocal OUT shadow footprint.
    """
    mock_migrator.board.clear()
    mock_state_schema.compositions.clear()
    mock_state_schema.objects.doors.append(
        DoorState(
            id="panel",
            name="standalone-door",
            layer="0",
            outlayer="dungeon-layer",
            material="neutral",
            position=Position(128, 256),
            out=Position(32, 64),
        )
    )
    monkeypatch.setattr(
        "app.services.orchestration.migrator.Loader.load_state",
        lambda _: mock_state_schema,
    )

    mock_migrator.target = testbed
    for _ in mock_migrator._build_generator():
        pass

    in_doors = mock_migrator.board.instances(AssetInstances.DOORS.value, "0")
    out_doors = mock_migrator.board.instances(
        AssetInstances.DOORS.value, "dungeon-layer"
    )

    assert len(in_doors) == 1
    assert in_doors[0].name == "standalone-door"
    assert in_doors[0].state.projection == LayerProjections.IN.value

    assert len(out_doors) == 1
    assert out_doors[0].name == "standalone-door-out"
    assert out_doors[0].state.projection == LayerProjections.OUT.value
    assert out_doors[0].state.outlayer == "0"


@pytest.mark.workflow_plots
@pytest.mark.workflow_seasons
@pytest.mark.workflow_fluids
def test_migrator_build_generator_assets_and_post_hydration(
    mock_migrator,
    mock_properties_schema,
    testbed,
):
    """
    Verifies Migrator hydrates PlotState, CalendarState, Player properties from
    sheets.sprites, Perimeters across all layers, and pumps initial Fluids.
    """
    mock_migrator.board.clear()
    mock_migrator.target = testbed

    for _ in mock_migrator._build_generator():
        pass

    assert len(mock_migrator.board.assets()) > 0
    assert mock_migrator.current == mock_migrator.maximum

    # 1. PlotState & CalendarState hydration
    assert mock_migrator.board.plot.current == "castle-dawn-locked"
    assert mock_migrator.board.calendar.season == Seasons.SPRING.value

    # 2. Player property lookup mapped to sheets.sprites["player"]
    player = mock_migrator.board.player()
    assert player is not None
    assert player.category == AssetCategories.SHEETS.value
    assert player.instance == AssetInstances.PLAYERS.value
    assert player.properties is mock_properties_schema.sheets.sprites["player"]

    # 3. Post-Hydration Perimeters & Fluid propagation
    for layer in mock_migrator.board.layers():
        assert len(mock_migrator.board.perimeters.get(layer, [])) > 0

    fluids = mock_migrator.board.instances(AssetInstances.FLUIDS.value, "0")
    assert len(fluids) == 2
    for fluid in fluids:
        assert fluid.state.length > 0
        assert len(fluid.state.hitboxes) > 0