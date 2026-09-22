"""
# Ontology: tests.unit.test_app_services_generators_game_actuator
"""
# Test Libraries
from tests.unit.conftest import DummyFrame, DummyAnimation

# Application Libraries
from app.assets.base import (
    Asset, 
    Taxonomy
)
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.models.properties import ObjectProperties
from app.models.state.objects import (
    PositionalState, 
    SwitchState
)
from app.services.generators.game.actuator import Actuator

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox, 
    Velocity
)


def test_actuator_pump_down_to_boundary(mock_fluid_board):
    """
    Verify downward propagation truncates at boundary wall and does not pool.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    # Remove crate to ensure boundary is struck
    crate = board.instances(AssetInstances.CRATES.value)[0]
    board.remove([crate])

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, board)

    assert length == 319
    assert pool is None
    assert len(hitboxes) == 1
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 319
    assert fluid.state.dirty is False

def test_actuator_upstream_obstacles_ignored(mock_fluid_board):
    """
    Verify obstacles positioned at or behind emitter origin are not struck.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=50)
    fluid.state.source = Directions.DOWN

    # Upstream crate
    crate_up_tax = Taxonomy("crate-up", "crate-up", AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    crate_up_props = ObjectProperties(dimensions=Dimensions(w=32, l=32), mass=5)
    crate_up_state = PositionalState(id="crate-up", layer="0", position=Position(x=70, y=10))
    crate_up = Asset(crate_up_tax, crate_up_props, crate_up_state, DummyFrame(), DummyAnimation())

    # Downstream crate
    crate_down = board.instances(AssetInstances.CRATES.value)[0]
    crate_down.state.position = Position(x=70, y=150)

    board.add([crate_up])

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, board)

    assert length == 100
    assert fluid.state.length == 100


def test_actuator_open_gate_not_occluding(mock_fluid_board):
    """
    Verify open gates (switch=True) are bypassed during raycast truncation.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    gate_tax = Taxonomy("gate-1", "gate", AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    gate_props = ObjectProperties(dimensions=Dimensions(w=32, l=32), mass=0)
    gate_state = SwitchState(id="gate-1", layer="0", position=Position(x=70, y=60), switch=True)
    gate = Asset(gate_tax, gate_props, gate_state, DummyFrame(), DummyAnimation())
    board.add([gate])

    crate = board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=120)

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, board)

    assert length == 120


def test_actuator_character_sheets_ignored(mock_fluid_board, mock_board_assets):
    """
    Verify characters (SHEETS) do not obstruct fluid raycasts.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    sprite = mock_board_assets[0]
    sprite.state.position = Position(x=70, y=40)
    board.add([sprite])

    crate = board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=120)

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, board)

    assert length == 120

def test_actuator_pump_down_to_obstacle_with_pool(mock_fluid_board):
    """
    Verify internal obstacle collision truncates stream and forms a solid annular pool.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN
    fluid.state.flow = 2

    crate = board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=96)
    crate.properties.dimensions = Dimensions(w=32, l=32)

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, board)

    assert length == 96
    assert pool is not None
    # Pool bounds: ox - 2*32 = 6, oy - 2*32 = 32, ow + 4*32 = 160, ol + 4*32 = 160
    assert pool.x == 6
    assert pool.y == 32
    assert pool.w == 160
    assert pool.l == 160

    # 1 stream hitbox + 1 solid pool hitbox covering outer flood extent
    assert len(hitboxes) == 2
    assert hitboxes[0].dimensions.w == 32
    assert hitboxes[0].dimensions.l == 96
    assert hitboxes[1].position.x == -64  # pool.x - fluid.x (6 - 70)
    assert hitboxes[1].position.y == 32   # pool.y - fluid.y (32 - 0)
    assert hitboxes[1].dimensions.w == 160
    assert hitboxes[1].dimensions.l == 160


def test_actuator_rafts_ignored_as_obstacles(mock_fluid_board, mock_raft):
    """
    Verify rafts (RAFTS) bypass raycast truncation and do not occlude fluids.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    mock_raft.state.position = Position(x=70, y=40)
    board.add([mock_raft])

    crate = board.instances(AssetInstances.CRATES.value)[0]
    crate.state.position = Position(x=70, y=120)

    actuator = Actuator()
    length, pool, hitboxes = actuator.pump(fluid, board)

    # Stream ignores raft at y=40 and truncates on crate at y=120
    assert length == 120


def test_actuator_pump_does_not_mutate_shared_properties(mock_fluid_board):
    """
    Verify Actuator.pump does not mutate shared EffectProperties.hitboxes.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.properties.hitboxes = []

    actuator = Actuator()
    actuator.pump(fluid, board)

    assert fluid.properties.hitboxes == []