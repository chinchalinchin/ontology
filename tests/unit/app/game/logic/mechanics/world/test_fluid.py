"""
# Ontology: tests.unit.app.game.logic.mechanics.world.test_fluid.py
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetInstances,
    Relations,
    Directions
)
from app.game.logic.mechanics.world.fluid import FluidMechanics
from app.models.state.assets.effects import Branch

# Cython Libraries
from libs.core.models import (
    Position, 
    Velocity
)


@pytest.mark.fluids
def test_fluid_mechanics_early_exit_no_fluids(mock_board, mock_bus):
    """
    Verify mechanic yields immediately when no fluids are instantiated.
    """
    fluids = mock_board.instances(AssetInstances.FLUIDS.value)
    mock_board.remove(fluids)

    mechanic = FluidMechanics()
    mechanic.update(mock_board, 0.016, mock_bus, None)


@pytest.mark.fluids
def test_fluid_mechanics_steady_state_no_invalidation(mock_board, mock_bus):
    """
    Verify stationary obstacles do not re-flag clean fluids as dirty.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    crate.state.velocity = Velocity(vx=0.0, vy=0.0)
    fluid.state.dirty = False

    mechanic = FluidMechanics()

    # Initial frame records state
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert fluid.state.dirty is False

    # Second frame confirms steady-state
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert fluid.state.dirty is False


@pytest.mark.fluids
def test_fluid_mechanics_dynamic_bodies_do_not_invalidate_fluid(mock_board, mock_bus):
    """
    Verify dynamic bodies (mass > 0, like Crates) do not invalidate fluid propagation
    when moving (Fix B011).
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    crate.state.position = Position(x=70, y=96)
    crate.state.velocity = Velocity(vx=0.0, vy=0.0)

    mechanic = FluidMechanics()

    # Initialize mechanic state on frame 1
    mechanic.update(mock_board, 0.016, mock_bus, None)
    assert fluid.state.dirty is False

    # Imparting velocity to a dynamic crate does NOT mark fluid dirty
    crate.state.velocity = Velocity(vx=2.0, vy=0.0)
    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert fluid.state.dirty is False


@pytest.mark.fluids
def test_fluid_mechanics_gate_switch_toggle_invalidates(mock_board, mock_bus):
    """
    Verify static gate switch transitions invalidate fluid flow and re-propagate length.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.flow = 0
    gate = mock_board.instances(AssetInstances.GATES.value)[0]

    # Start with closed gate at y=60
    gate.state.switch = False
    gate.state.position = Position(x=70, y=60)

    mechanic = FluidMechanics()
    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert fluid.state.dirty is False
    assert fluid.state.length == 60

    # Opening gate invalidates layer and allows stream to propagate to boundary (y=319)
    gate.state.switch = True
    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert fluid.state.dirty is False 
    assert fluid.state.length == 319


@pytest.mark.fluids
def test_fluid_mechanics_cross_layer_isolation(mock_board, mock_bus):
    """
    Verify obstacle movements on layer 1 do not invalidate fluids on layer 0.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.layer = "0"
    fluid.state.dirty = False

    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    gate.state.layer = "1"
    gate.state.switch = False

    mechanic = FluidMechanics()

    mechanic.update(mock_board, 0.016, mock_bus, None)

    gate.state.switch = True
    mechanic.update(mock_board, 0.016, mock_bus, None)

    assert fluid.state.dirty is False


@pytest.mark.fluids
def test_fluid_mechanics_two_pass_layer_shorelines(
    mock_board, 
    mock_bus, 
    mock_actuator, 
    mock_shoreline_index
):
    """
    Verify FluidMechanics executes coordinated two-pass update, synthesizing
    layer-wide shorelines on Board via Cartographer.
    """
    mechanic = FluidMechanics(actuator=mock_actuator)
    mechanic.set_relation(Relations.SHORELINES.value, mock_shoreline_index)

    mechanic.update(mock_board, 0.016, mock_bus, None)

    shores = mock_board.shorelines("0")
    assert len(shores) > 0
    for shore in shores:
        assert shore.instance == AssetInstances.SHORELINES.value
        assert shore.state.layer == "0"


@pytest.mark.fluids
def test_board_water_subtile_precision(mock_board):
    """
    Verify Board.water broad/narrow spatial hash returns False for coordinates
    sharing a 32px tile bucket with fluid but falling outside exact bounds.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 64
    fluid.state.pool = None

    mock_board.update_fluid_cache("0")

    # Inside stream corridor: x in [70, 102), y in [0, 64)
    assert mock_board.fluid("0", Position(70, 10)) is True
    assert mock_board.fluid("0", Position(101, 10)) is True

    # Same tile bucket (cx = 69 // 32 = 2, cy = 10 // 32 = 0) but outside corridor
    assert mock_board.fluid("0", Position(69, 10)) is False
    assert mock_board.fluid("0", Position(102, 10)) is False


@pytest.mark.fluids
def test_board_fluid_spatial_hash_indexes_child_branches(mock_board):
    """
    Verify Board broad/narrow spatial water checking detects Cartesian points
    located inside active child branch corridors.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN.value
    fluid.state.length = 32

    # Attach secondary child branch discharging at (0, 192) flowing DOWN
    fluid.state.branches = [
        Branch(
            position=Position(x=0, y=192),
            source=Directions.DOWN.value,
            flow=1,
            length=100
        )
    ]

    mock_board.update_fluid_cache("0")

    # Coordinate inside child branch corridor: x in [0, 32), y in [192, 292)
    assert mock_board.fluid("0", Position(10, 200)) is True
    assert mock_board.fluid("0", Position(0, 192)) is True

    # Coordinate outside branch corridor
    assert mock_board.fluid("0", Position(35, 200)) is False
    assert mock_board.fluid("0", Position(10, 300)) is False


@pytest.mark.fluids
def test_board_bridges_query_excludes_obstacles_and_weights(mock_board, mock_bridge):
    """
    Verify Board.bridges() returns sensor bridge assets while strictly excluding
    them from board.obstacles() and board.weights().
    """
    mock_board.add([mock_bridge])

    bridges = mock_board.bridges("0")
    assert mock_bridge in bridges

    # Bridges are sensors (mass = -1) and must not pollute pathfinding or weights
    assert mock_bridge not in mock_board.obstacles("0")
    assert mock_bridge not in mock_board.weights("0")