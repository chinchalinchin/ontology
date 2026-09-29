"""
# Ontology: tests.unit.services.generators.game.test_actuator
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetInstances,
    Directions
)
from libs.core.models import (
    Position, 
)


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_pump_down_to_boundary(mock_board, mock_actuator):
    """
    Verify downward propagation truncates at boundary wall and does not pool.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 319
    assert pool is None
    assert len(hitboxes) == 1
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 319
    assert fluid.state.dirty is False


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_upstream_obstacles_ignored(mock_board, mock_actuator):
    """
    Verify obstacles positioned at or behind emitter origin are not struck.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=50)
    fluid.state.source = Directions.DOWN

    # Upstream static strut (mass=0) at y=10
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    strut.state.position = Position(x=70, y=10)

    # Downstream closed static gate (mass=0) at y=150
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=150)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    # 150 - 50 = 100
    assert length == 100
    assert fluid.state.length == 100


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_open_gate_not_occluding(mock_board, mock_actuator):
    """
    Verify open gates (switch=True) are bypassed during raycast truncation.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    # Open gate at y=60
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = True
    gate.state.position = Position(x=70, y=60)

    # Downstream static strut (mass=0) at y=120
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    strut.state.position = Position(x=70, y=120)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 120


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_character_sheets_ignored(mock_board, mock_actuator):
    """
    Verify characters (SHEETS) do not obstruct fluid raycasts.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    player = mock_board.player()
    player.state.position = Position(x=70, y=40)

    # Downstream static strut (mass=0) at y=120
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    strut.state.position = Position(x=70, y=120)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 120


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_dynamic_bodies_ignored_as_obstacles(mock_board, mock_crate, mock_actuator):
    """
    Verify dynamic bodies (mass > 0, such as Crates) do not occlude fluids (Fix B011).
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    # Dynamic crate (mass=5) placed in the stream corridor
    mock_crate.state.position = Position(x=70, y=96)
    mock_board.add([mock_crate])

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    # Stream ignores dynamic body and continues to boundary at y=319
    assert length == 319
    assert pool is None


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_pump_down_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify internal static obstacle (mass=0) collision truncates stream and forms annular pool.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN
    fluid.state.flow = 2

    # Closed gate (mass=0, dimensions 32x32) at y=96
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=96)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 96
    assert pool is not None
    # Pool bounds snapped to 32px tile grid:
    # X: [70 - 64, 70 + 32 + 64] = [6, 166] -> snapped [0, 192], w = 192
    # Y: [96 - 64, 96 + 32 + 64] = [32, 192] -> snapped [32, 192], l = 160
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
@pytest.mark.services
def test_actuator_rafts_ignored_as_obstacles(mock_board, mock_raft, mock_actuator):
    """
    Verify rafts (RAFTS) bypass raycast truncation and do not occlude fluids.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    mock_raft.state.position = Position(x=70, y=40)

    # Downstream static barrier (mass=0) at y=120
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=120)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    # Stream ignores raft at y=40 and truncates on closed gate at y=120
    assert length == 120


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_closed_gate_occludes_stream(mock_board, mock_actuator):
    """
    Verify closed gates (switch=False, mass=0) occlude raycasts and truncate fluid flow.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=60)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 60
    assert fluid.state.length == 60


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_pump_does_not_mutate_shared_properties(mock_board, mock_actuator):
    """
    Verify Actuator.pump does not mutate shared EffectProperties.hitboxes.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.properties.hitboxes = []

    mock_actuator.pump(fluid, mock_board)

    assert fluid.properties.hitboxes == []