"""
@domain.test
@test.unit
@app.services
@workflow.generation
@workflow.fluids

# Ontology: Tests - tests.unit.services.generators.game.test_actuator

Unit tests for the Actuator service.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Directions,
)
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_fluids,
]

# -----------------------------------------------------

def test_actuator_pump_down_to_boundary(mock_board, mock_actuator):
    """
    Verify unobstructed downward propagation truncates at boundary wall and does not pool.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(x=1200, y=0)
    fluid.state.source = Directions.DOWN.value

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length > 0
    assert pool is None
    assert len(hitboxes) == 1
    assert hitboxes[0].dimensions.w == fluid.properties.dimensions.w
    assert hitboxes[0].dimensions.l == length
    assert fluid.state.dirty is False


def test_actuator_upstream_obstacles_ignored(mock_board, mock_actuator):
    """
    Verify obstacles positioned at or behind emitter origin are not struck.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=50)
    fluid.state.source = Directions.DOWN.value

    strut = mock_board.instances(AssetInstances.STRUTS.value, "0")[0]
    strut.state.position = Position(x=70, y=10)

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=150)

    length, pool, _ = mock_actuator.pump(fluid, mock_board)

    assert length == gate.state.position.y - fluid.state.position.y
    assert pool is None


def test_actuator_open_gate_not_occluding(mock_board, mock_actuator):
    """
    Verify open gates (switch=True) are bypassed during raycast truncation.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = True
    gate.state.position = Position(x=70, y=60)

    strut = mock_board.instances(AssetInstances.STRUTS.value, "0")[0]
    strut.state.position = Position(x=70, y=120)

    length, _, _ = mock_actuator.pump(fluid, mock_board)

    assert length == strut.state.position.y


def test_actuator_character_sheets_ignored(mock_board, mock_actuator):
    """
    Verify characters (SHEETS) do not obstruct fluid raycasts.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    player = mock_board.player()
    player.state.position = Position(x=70, y=40)

    strut = mock_board.instances(AssetInstances.STRUTS.value, "0")[0]
    strut.state.position = Position(x=70, y=120)

    length, _, _ = mock_actuator.pump(fluid, mock_board)

    assert length == strut.state.position.y


def test_actuator_dynamic_bodies_ignored_as_obstacles(mock_board, mock_actuator):
    """
    Verify dynamic bodies (mass > 0, such as Crates) do not occlude fluids.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(x=1200, y=0)
    fluid.state.source = Directions.DOWN.value

    mock_crate = mock_board.instances(AssetInstances.CRATES.value, "0")[0]
    mock_crate.state.position = Position(x=1200, y=96)

    length, pool, _ = mock_actuator.pump(fluid, mock_board)

    assert length > mock_crate.state.position.y + mock_crate.dimensions.l
    assert pool is None


def test_actuator_pump_down_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify single-intensity fluid (flow=1) striking a static obstacle truncates at
    the pool margin and emits non-overlapping stream and annular pool hitboxes without branching.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.flow = 1

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=96)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert length == 64
    assert pool is not None
    assert pool.x == -96
    assert pool.y == 64
    assert pool.w == 384
    assert pool.l == 128

    assert len(hitboxes) == 2
    assert hitboxes[0].dimensions.w == fluid.properties.dimensions.w
    assert hitboxes[0].dimensions.l == length
    assert hitboxes[1].position.x == pool.x - fluid.state.position.x
    assert hitboxes[1].position.y == pool.y - fluid.state.position.y
    assert hitboxes[1].dimensions.w == pool.w
    assert hitboxes[1].dimensions.l == pool.l
    assert len(fluid.state.branches) == 0


def test_actuator_bifurcation_downstream_flanks(mock_board, mock_actuator):
    """
    Verify multi-intensity fluid (flow=2) striking a static obstacle forms an annular pool,
    discharges child streams along lateral flanks from the downstream pool margin, and
    compiles compound relative hitboxes.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.flow = 2

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=96)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)
    fw = fluid.properties.dimensions.w

    assert length == 32
    assert pool is not None
    assert pool.x == -192
    assert pool.y == 32
    assert pool.w == 576
    assert pool.l == 192

    assert len(hitboxes) == 4
    assert len(fluid.state.branches) == 2

    left_branch, right_branch = fluid.state.branches
    assert left_branch.position.x == pool.x
    assert left_branch.position.y == pool.y + pool.l
    assert left_branch.source == Directions.DOWN.value
    assert left_branch.flow == 1
    assert left_branch.length > 0

    assert right_branch.position.x == pool.x + pool.w - fw
    assert right_branch.position.y == pool.y + pool.l
    assert right_branch.source == Directions.DOWN.value
    assert right_branch.flow == 1
    assert right_branch.length > 0

    assert hitboxes[0].dimensions.w == fw
    assert hitboxes[0].dimensions.l == length
    assert hitboxes[1].position.x == pool.x - fluid.state.position.x
    assert hitboxes[1].position.y == pool.y - fluid.state.position.y
    assert hitboxes[2].position.x == left_branch.position.x - fluid.state.position.x
    assert hitboxes[2].position.y == left_branch.position.y - fluid.state.position.y
    assert hitboxes[2].dimensions.w == fw
    assert hitboxes[2].dimensions.l == left_branch.length
    assert hitboxes[3].position.x == right_branch.position.x - fluid.state.position.x
    assert hitboxes[3].position.y == right_branch.position.y - fluid.state.position.y
    assert hitboxes[3].dimensions.w == fw
    assert hitboxes[3].dimensions.l == right_branch.length


def test_actuator_rafts_ignored_as_obstacles(mock_board, mock_actuator):
    """
    Verify Rafts bypass raycast truncation and do not occlude fluids.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    raft = mock_board.instances(AssetInstances.RAFTS.value, "0")[0]
    raft.state.position = Position(x=70, y=40)

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=120)

    length, _, _ = mock_actuator.pump(fluid, mock_board)

    assert length == gate.state.position.y


def test_actuator_closed_gate_occludes_stream(mock_board, mock_actuator):
    """
    Verify closed gates (switch=False, mass=0) occlude raycasts and truncate fluid flow.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.flow = 0
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=60)

    length, _, _ = mock_actuator.pump(fluid, mock_board)

    assert length == gate.state.position.y
    assert fluid.state.length == gate.state.position.y


def test_actuator_pump_does_not_mutate_shared_properties(mock_board, mock_actuator):
    """
    Verify Actuator.pump does not mutate shared EffectProperties.hitboxes.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.properties.hitboxes = []

    mock_actuator.pump(fluid, mock_board)

    assert fluid.properties.hitboxes == []


def test_actuator_pump_left_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify westward propagation truncates stream length at East pool margin.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(x=296, y=500)
    fluid.state.source = Directions.LEFT.value
    fluid.state.flow = 1

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=100, y=500)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert pool is not None
    assert pool.x + pool.w == 288
    assert length == 8
    assert hitboxes[0].dimensions.w == 8
    assert hitboxes[0].position.x == -8


def test_actuator_pump_up_to_obstacle_with_pool(mock_board, mock_actuator):
    """
    Verify northward propagation truncates stream length at South pool margin.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state.position = Position(x=70, y=232)
    fluid.state.source = Directions.UP.value
    fluid.state.flow = 1

    gate = mock_board.instances(AssetInstances.GATES.value, "0")[0]
    gate.state.switch = False
    gate.state.position = Position(x=70, y=100)

    length, pool, hitboxes = mock_actuator.pump(fluid, mock_board)

    assert pool is not None
    assert pool.y + pool.l == 224
    assert length == 8
    assert hitboxes[0].dimensions.l == 8
    assert hitboxes[0].position.y == -8


def test_actuator_propagate_clears_cached_frame_keys(mock_board, mock_actuator):
    """
    Verify Actuator.propagate clears fluid state frame key cache slots (Fix B014).
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value, "0")[0]
    fluid.state._keys[0] = [("stale-key", 0, 0)]

    mock_actuator.propagate(fluid, mock_board)

    assert len(fluid.state._keys) == 0