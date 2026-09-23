"""
# Ontology: tests.unit.test_app_services_generators_game_actuator
"""
# Test Libraries
from tests.unit.conftest import (
    DummyFrame, 
    DummyAnimation
)

# Application Libraries
from app.assets.base import (
    Asset, 
    Taxonomy
)
from app.assets.frames import (
    FluidFrame
)
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Directions
)
from app.models.properties import (
    ObjectProperties,
    EffectProperties
)
from app.models.groups import (
    SpawnableGroup
)
from app.models.state import (
    PositionalState, 
    SwitchState,
    FluidState
)
from app.services.generators.game import (
    Actuator,
    Cradle
)

from app.game.logic.relations import ShorelineIndex

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions
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

def test_actuator_generates_and_purges_shorelines(mock_fluid_board, mock_geography_properties, mock_recipes):
    """
    Verify Actuator generates shorelines on unoccluded flanks and purges them on re-pump.
    """
    board = mock_fluid_board
    fluid = board.instances(AssetInstances.FLUIDS.value)[0]
    fluid.state.position = Position(x=70, y=0)
    fluid.state.source = Directions.DOWN

    # Setup Cradle and ShorelineIndex
    spawnables = SpawnableGroup(
        projectiles={}, expressions={}, collectables={},
        hazards={}, passive={}, struts={},
        shorelines={"grassy-shore": mock_geography_properties}
    )
    board.cradle = Cradle(spawnables, mock_recipes, None)
    shoreline_index = ShorelineIndex({("tile-1", "waterflow-1"): "grassy-shore"})

    actuator = Actuator(shorelines=shoreline_index)
    actuator.pump(fluid, board)

    shorelines = board.instances(AssetInstances.SHORELINES.value, "0")
    assert len(shorelines) > 0
    assert len(fluid.state.shorelines) == len(shorelines)

    # Initial child shoreline names
    first_shoreline_names = set(fluid.state.shorelines)

    # Re-pump should purge old shorelines and regenerate without duplicate asset names
    actuator.pump(fluid, board)
    current_shoreline_names = set(fluid.state.shorelines)

    # Ensure none of the old child entities remain on the board
    for old_name in first_shoreline_names:
        assert board.asset(old_name, "0") is None

    assert len(current_shoreline_names) > 0


def test_actuator_water_meeting_water_suppresses_shorelines(mock_fluid_board, mock_geography_properties, mock_recipes):
    """
    Verify that when water meets water across overlapping fluid bounds,
    internal shoreline generation is suppressed.
    """
    board = mock_fluid_board
    fluid1 = board.instances(AssetInstances.FLUIDS.value)[0]

    # Spawn second adjacent fluid covering the full height of the corridor
    tax2 = Taxonomy("waterflow-1", "fluid-2", AssetCategories.EFFECTS.value, AssetInstances.FLUIDS.value)
    props2 = EffectProperties(dimensions=Dimensions(w=32, l=32), count=3, mass=-1)
    state2 = FluidState(
        id="waterflow-1",
        name="fluid-2",
        layer="0",
        position=Position(x=102, y=0),  # Adjacent directly to East flank of fluid1
        source=Directions.DOWN.value,
        flow=1,
        length=320
    )
    fluid2 = Asset(tax2, props2, state2, FluidFrame(), DummyAnimation())
    board.add([fluid2])

    spawnables = SpawnableGroup(
        projectiles={}, expressions={}, collectables={},
        hazards={}, passive={}, struts={},
        shorelines={"grassy-shore": mock_geography_properties}
    )
    board.cradle = Cradle(spawnables, mock_recipes, None)
    shoreline_index = ShorelineIndex({("tile-1", "waterflow-1"): "grassy-shore"})

    actuator = Actuator(shorelines=shoreline_index)
    actuator.pump(fluid1, board)

    # Fluid1 East flank directly touches Fluid2 water: East shoreline (RIGHT) is suppressed
    shorelines = [board.asset(name, "0") for name in fluid1.state.shorelines if board.asset(name, "0")]
    right_shorelines = [s for s in shorelines if s.state.orientation == Directions.RIGHT.value]
    assert len(right_shorelines) == 0