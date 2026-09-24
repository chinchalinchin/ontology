"""
# Ontology: tests.unit.test_app_game_logic_mechanics_world_fluid
"""
import collections
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.assets.base import Asset, Taxonomy
from app.game.logic.mechanics.world.fluid import FluidMechanics
from app.models.properties import ObjectProperties
from app.models.state.objects import SwitchState
from libs.core.models import Position, Dimensions, Velocity
from tests.unit.conftest import DummyFrame, DummyAnimation


def test_fluid_mechanics_early_exit_no_fluids(mock_board):
    """
    Verify mechanic yields immediately when no fluids are instantiated.
    """
    mechanic = FluidMechanics()
    bus = collections.deque()
    mechanic.update(mock_board, 0.016, bus, None)


def test_fluid_mechanics_steady_state_no_invalidation(mock_board):
    """
    Verify stationary obstacles do not re-flag clean fluids as dirty.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    crate.state.velocity = Velocity(vx=0.0, vy=0.0)
    fluid.state.dirty = False

    mechanic = FluidMechanics()
    bus = collections.deque()

    # Initial frame records state
    mechanic.update(mock_board, 0.016, bus, None)
    assert fluid.state.dirty is False

    # Second frame confirms steady-state
    mechanic.update(mock_board, 0.016, bus, None)
    assert fluid.state.dirty is False


def test_fluid_mechanics_crate_velocity_triggers_invalidation(mock_board):
    """
    Verify moving crate marks fluid on that layer dirty and invokes Actuator.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    crate.state.position = Position(x=70, y=96)
    crate.state.velocity = Velocity(vx=0.0, vy=0.0)
    fluid.state.dirty = False

    mechanic = FluidMechanics()
    bus = collections.deque()

    mechanic.update(mock_board, 0.016, bus, None)

    crate.state.velocity = Velocity(vx=2.0, vy=0.0)
    mechanic.update(mock_board, 0.016, bus, None)

    assert fluid.state.dirty is False
    assert fluid.state.length == 80


def test_fluid_mechanics_gate_switch_toggle_invalidates(mock_board):
    """
    Verify gate switch transitions invalidate fluid flow.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    gate = mock_board.instances(AssetInstances.GATES.value)[0]

    fluid.state.dirty = False

    mechanic = FluidMechanics()
    bus = collections.deque()

    mechanic.update(mock_board, 0.016, bus, None)

    gate.state.switch = True
    mechanic.update(mock_board, 0.016, bus, None)

    assert fluid.state.dirty is False 


def test_fluid_mechanics_cross_layer_isolation(mock_board):
    """
    Verify obstacle movements on layer 1 do not invalidate fluids on layer 0.
    """
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.layer = "0"
    fluid.state.dirty = False

    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.layer = "1"
    crate.state.velocity = Velocity(vx=5.0, vy=0.0)

    mechanic = FluidMechanics()
    bus = collections.deque()

    mechanic.update(mock_board, 0.016, bus, None)
    assert fluid.state.dirty is False