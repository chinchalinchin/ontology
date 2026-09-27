"""
# Ontology: tests.unit.test_app_services_generators_game_actuator
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetInstances,
    Directions
)
from app.services.generators.game import (
    Actuator
)

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions
)


@pytest.mark.fluids
def test_actuator_pump_down_to_boundary(mock_board):
    """
    Verify downward propagation truncates at boundary wall and does not pool.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    # Remove crate to ensure boundary is struck
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    mock_board.remove([crate])

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, mock_board)

    assert length == 319
    assert pool is None
    assert len(hitboxes) == 1
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 319
    assert fluid.state.dirty is False


@pytest.mark.fluids
def test_actuator_upstream_obstacles_ignored(mock_board, mock_crate_alt, mock_actuator):
    """
    Verify obstacles positioned at or behind emitter origin are not struck.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=50)
    fluid.state.source = Directions.DOWN

    # Upstream crate via fixture
    mock_board.add([mock_crate_alt])

    # Downstream crate
    crate_down = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate_down.state.position = Position(x=70, y=150)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 100
    assert fluid.state.length == 100


@pytest.mark.fluids
def test_actuator_open_gate_not_occluding(mock_board, mock_actuator):
    """
    Verify open gates (switch=True) are bypassed during raycast truncation.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    # Use existing gate fixture on the board
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = True
    gate.state.position = Position(x=70, y=60)

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=120)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 120


@pytest.mark.fluids
def test_actuator_character_sheets_ignored(mock_board, mock_actuator):
    """
    Verify characters (SHEETS) do not obstruct fluid raycasts.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    player = mock_board.player()
    player.state.position = Position(x=70, y=40)

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=120)

    actuator = Actuator()
    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 120


@pytest.mark.fluids
def test_actuator_pump_down_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify internal obstacle collision truncates stream and forms a solid annular pool.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN
    fluid.state.flow = 2

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=96)
    crate.properties.dimensions = Dimensions(w=32, l=32)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 96
    assert pool is not None
    # Pool bounds snapped to 32px tile grid:
    # X: [6, 166] -> snapped to [0, 192], width = 192
    # Y: [32, 192] -> snapped to [32, 192], length = 160
    assert pool.x == 0
    assert pool.y == 32
    assert pool.w == 192
    assert pool.l == 160

    # 1 stream hitbox + 1 solid pool hitbox covering outer flood extent
    assert len(hitboxes) == 2
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 96
    assert hitboxes[1].position.x == -70  # pool.x - fluid.x (0 - 70)
    assert hitboxes[1].position.y == 32   # pool.y - fluid.y (32 - 0)
    assert hitboxes[1].dimensions.w == 192
    assert hitboxes[1].dimensions.l == 160


@pytest.mark.fluids
def test_actuator_rafts_ignored_as_obstacles(mock_board, mock_raft, mock_actuator):
    """
    Verify rafts (RAFTS) bypass raycast truncation and do not occlude fluids.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    mock_raft.state.position = Position(x=70, y=40)

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=120)


    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    # Stream ignores raft at y=40 and truncates on crate at y=120
    assert length == 120


@pytest.mark.fluids
def test_actuator_pump_does_not_mutate_shared_properties(mock_board, mock_actuator):
    """
    Verify Actuator.pump does not mutate shared EffectProperties.hitboxes.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.properties.hitboxes = []

    mock_actuator.pump(fluid, mock_board)

    assert fluid.properties.hitboxes == []


@pytest.mark.fluids
def test_actuator_generates_and_purges_shorelines(
    mock_board, 
    mock_actuator
):
    """
    Verify Actuator generates shorelines on unoccluded flanks and purges them on re-pump.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    mock_actuator.pump(fluid, mock_board)

    shorelines = mock_board.instances(AssetInstances.SHORELINES.value, "0")
    assert len(shorelines) > 0
    assert len(fluid.state.shorelines) == len(shorelines)

    # Initial child shoreline names
    first_shoreline_names = set(fluid.state.shorelines)

    # Re-pump should purge old shorelines and regenerate without duplicate asset names
    mock_actuator.pump(fluid, mock_board)
    current_shoreline_names = set(fluid.state.shorelines)

    # Ensure none of the old child entities remain on the board
    for old_name in first_shoreline_names:
        assert mock_board.asset(old_name, "0") is None

    assert len(current_shoreline_names) > 0


@pytest.mark.fluids
def test_actuator_water_meeting_water_suppresses_shorelines(
    mock_board,
    mock_actuator,
    mock_fluid_adjacent
):
    """
    Verify that when water meets water across overlapping fluid bounds,
    internal shoreline generation is suppressed.
    """
    fluid1 = mock_board.instances(AssetInstances.FLUIDS.value)[0]

    # Add adjacent fluid fixture directly touching East flank of fluid1
    mock_board.add([mock_fluid_adjacent])

    mock_actuator.pump(fluid1, mock_board)

    # Fluid1 East flank directly touches Fluid2 water: East shoreline (RIGHT) is suppressed
    shorelines = [
        mock_board.asset(name, "0")
        for name in fluid1.state.shorelines
        if mock_board.asset(name, "0")
    ]
    right_shorelines = [
        s for s in shorelines
        if s.state.orientation == Directions.RIGHT.value
    ]
    assert len(right_shorelines) == 0