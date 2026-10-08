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
from libs.core.models import Position


@pytest.mark.fluids
@pytest.mark.services
@pytest.mark.ecology
def test_actuator_pump_down_to_boundary(mock_board, mock_actuator):
    """
    Verify downward propagation truncates at boundary wall and does not pool.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 319
    assert pool is None
    assert len(hitboxes) == 1
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 319
    assert fluid.state.dirty is False


@pytest.mark.fluids
@pytest.mark.services
@pytest.mark.ecology
def test_actuator_upstream_obstacles_ignored(mock_board, mock_actuator):
    """
    Verify obstacles positioned at or behind emitter origin are not struck.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=50)
    fluid.state.source = Directions.DOWN.value

    # Upstream static strut (mass=0) at y=10
    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    strut.state.position = Position(x=70, y=10)

    # Downstream closed static gate (mass=0) at y=150
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=150)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 100


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_open_gate_not_occluding(mock_board, mock_actuator):
    """
    Verify open gates (switch=True) are bypassed during raycast truncation.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = True
    gate.state.position = Position(x=70, y=60)

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
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    player = mock_board.player()
    player.state.position = Position(x=70, y=40)

    strut = mock_board.instances(AssetInstances.STRUTS.value)[0]
    strut.state.position = Position(x=70, y=120)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 120


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_dynamic_bodies_ignored_as_obstacles(mock_board, mock_crate, mock_actuator):
    """
    Verify dynamic bodies (mass > 0, such as Crates) do not occlude fluids.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    mock_crate.state.position = Position(x=70, y=96)
    mock_board.add([mock_crate])

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 319
    assert pool is None


@pytest.mark.fluids
@pytest.mark.services
@pytest.mark.ecology
def test_actuator_pump_down_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify single-intensity fluid (flow=1) striking a static obstacle truncates at
    the pool margin and emits non-overlapping stream and annular pool hitboxes without branching.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.flow = 1

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=96)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    # Stream terminates at pool margin (pool.y = 64)
    assert length == 64
    assert pool is not None
    assert pool.x == 32
    assert pool.y == 64
    assert pool.w == 128
    assert pool.l == 96

    # Exactly 2 hitboxes: stream corridor + solid annular pool
    assert len(hitboxes) == 2
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 64
    assert hitboxes[1].position.x == -38  # pool.x - fluid.x (32 - 70)
    assert hitboxes[1].position.y == 64   # pool.y - fluid.y (64 - 0)
    assert hitboxes[1].dimensions.w == 128
    assert hitboxes[1].dimensions.l == 96
    assert len(fluid.state.branches) == 0


@pytest.mark.fluids
@pytest.mark.services
@pytest.mark.ecology
def test_actuator_bifurcation_downstream_flanks(mock_board, mock_actuator):
    """
    Verify multi-intensity fluid (flow=2) striking a static obstacle forms an annular pool,
    discharges child streams along lateral flanks from the downstream pool margin, and
    compiles compound relative hitboxes.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.flow = 2

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=96)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    # Stream terminates at upstream pool margin (pool.y = 32)
    assert length == 32
    assert pool is not None
    assert pool.x == 0
    assert pool.y == 32
    assert pool.w == 192
    assert pool.l == 160

    # 4 hitboxes: stream corridor + annular pool + 2 lateral flank branches
    assert len(hitboxes) == 4
    assert len(fluid.state.branches) == 2

    # Left flank branch
    left_branch = fluid.state.branches[0]
    assert left_branch.position.x == 0
    assert left_branch.position.y == 192  # pool.y + pool.l
    assert left_branch.source == Directions.DOWN.value
    assert left_branch.flow == 1
    assert left_branch.length == 127      # 319 (boundary) - 192

    # Right flank branch
    right_branch = fluid.state.branches[1]
    assert right_branch.position.x == 160  # pool.x + pool.w - fw (0 + 192 - 32)
    assert right_branch.position.y == 192  # pool.y + pool.l
    assert right_branch.source == Directions.DOWN.value
    assert right_branch.flow == 1
    assert right_branch.length == 127      # 319 (boundary) - 192

    # Relative compound hitboxes
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 32
    assert hitboxes[1].position.x == -70
    assert hitboxes[1].position.y == 32
    assert hitboxes[2].position.x == -70  # left_branch.x - fluid.x (0 - 70)
    assert hitboxes[2].position.y == 192  # left_branch.y - fluid.y (192 - 0)
    assert hitboxes[2].dimensions.w == 32
    assert hitboxes[2].dimensions.l == 127
    assert hitboxes[3].position.x == 90   # right_branch.x - fluid.x (160 - 70)
    assert hitboxes[3].position.y == 192  # right_branch.y - fluid.y (192 - 0)
    assert hitboxes[3].dimensions.w == 32
    assert hitboxes[3].dimensions.l == 127


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_rafts_ignored_as_obstacles(mock_board, mock_raft, mock_actuator):
    """
    Verify rafts (RAFTS) bypass raycast truncation and do not occlude fluids.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    mock_raft.state.position = Position(x=70, y=40)

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=120)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 120


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_closed_gate_occludes_stream(mock_board, mock_actuator):
    """
    Verify closed gates (switch=False, mass=0) occlude raycasts and truncate fluid flow.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

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


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_pump_left_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify westward propagation truncates stream length at East pool margin.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=200, y=100)
    fluid.state.source = Directions.LEFT.value
    fluid.state.flow = 1

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=100, y=100)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert pool is not None
    assert pool.x + pool.w == 192
    assert length == 8
    assert hitboxes[0].dimensions.w == 8
    assert hitboxes[0].position.x == -8


@pytest.mark.fluids
@pytest.mark.services
@pytest.mark.ecology
def test_actuator_pump_up_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify northward propagation truncates stream length at South pool margin.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=200)
    fluid.state.source = Directions.UP.value
    fluid.state.flow = 1

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=100)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert pool is not None
    assert pool.y + pool.l == 192
    assert length == 8
    assert hitboxes[0].dimensions.l == 8
    assert hitboxes[0].position.y == -8


@pytest.mark.fluids
@pytest.mark.services
def test_actuator_propagate_clears_cached_frame_keys(mock_board, mock_actuator):
    """
    Verify Actuator.propagate clears fluid state frame key cache slots (Fix B014).
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    # Prime cache slot with synthetic pre-computed keys
    fluid.state._keys[0] = [("stale-key", 0, 0)]

    mock_actuator.propagate(fluid, mock_board)

    # Cache dictionary must be wiped clean upon physical geometry update
    assert len(fluid.state._keys) == 0