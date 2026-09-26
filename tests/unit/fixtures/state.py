"""
# Ontology: tests.unit.conftest
"""
# External Libraries
import pytest

# Application Libraries

from app.config.enums import ( 
    # -------- SPRITE FIELDS
    Intentions,
    Motivations,
    Directions,
    Goals,
)
from app.models.state import (
    # -------- SCHEMA
    StateSchema, 
    # -------- INSTANCES
    SheetStateInstances,
    ObjectStateInstances, 
    CraftStateInstances,
    TileStateInstances,
    EffectStateInstances,
    # -------- MODELS
    SpriteState,
    PlayerState,
    DoorState,
    MultiplierState,
    PropertyState,
    PositionalState,
    CollectionState,
    ShorelineState,
    FluidState,
    AnimationState,
    MotorState,
    SwitchState,
    # -------- FIELDS
    Inventory,
    Equipment,
    Mutators,
    MutatorTriggers,
    MutatorParameters,
    RadialParameters,
    FearParameters,
    Character,
    Goal,
    Psyche
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Multiple,
    Velocity,
    Hitbox,
)


# --------------------------------------------------------------------------
# -------------------------------------------------------------- MOCK STATES
# --------------------------------------------------------------------------

@pytest.fixture
def mock_property_state() -> PropertyState:
    return PropertyState(
        id="strut-castle", 
        name="castle", layer="0", 
        position=Position(x=250, y=250)
    )


@pytest.fixture
def mock_property_state_alt() -> PropertyState:
    return PropertyState(
        id="strut-wall",
        name="wall",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=0)
    )


@pytest.fixture
def mock_property_state_alt2() -> PropertyState:
    return PropertyState(
        id="strut-floor",
        name="floor",
        layer="brick-house-compose-layer",
        position=Position(x=0, y=96)
    )


@pytest.fixture
def mock_player_state() -> PlayerState:
    return PlayerState(
        id="player",
        name="player_1",
        layer="0",
        position=Position(x=10, y=10),
        character=Character(
            speed = 10,
            defense = 10,
            strength = 10
        )
    )


@pytest.fixture
def mock_sprite_state() -> SpriteState:
    return SpriteState(
        id="jasilynn",
        name="evil-empress-jasilynn",
        layer="brick-house-compose-layer",
        position=Position(x=175, y=200),
        intention=Intentions.FIND,
        psyche=Psyche(
            motivation=Motivations.CONQUEST.value, 
            persona="empress-jasilynn", 
            dialogue="greeting"
        ),
        mutators=Mutators(
            triggers=MutatorTriggers(vision=True),
            parameters=MutatorParameters(
                vision=RadialParameters(radius=128),
                action=RadialParameters(radius=25),
                fear=FearParameters(radius=128, limit=0.5, enemy=5),
                squeeze=RadialParameters(radius=10)
            )
        ),
        inventory=Inventory(equipment=Equipment()),
        animation=AnimationState(frame=0, tick=1)
    )


@pytest.fixture
def mock_sprite_state_alt() -> SpriteState:
    return SpriteState(
        id="sprite", 
        name="npc", 
        layer="0",
        position=Position(60, 50),
        intention=Intentions.FIND,
        goal=Goal(
            name="evil-empress-jasilynn", 
            category=Goals.POSITION.value, 
            layer="0", 
            position=Position(0, 50)
        ),
        mutators=Mutators(
            triggers=MutatorTriggers(vision=True),
            parameters=MutatorParameters(
                vision=RadialParameters(radius=128),
                action=RadialParameters(radius=25),
                fear=FearParameters(radius=128, limit=0.5, enemy=5),
                squeeze=RadialParameters(radius=10)
            )
        ),
        character=Character(
            speed=10
        ),
        velocity=Velocity(-10.0, 0.0),
        inventory=Inventory(
            equipment=Equipment()
        ),
        animation=AnimationState()
    )


@pytest.fixture
def mock_multiplier_state() -> MultiplierState:
    return MultiplierState(
        id="tile-1",
        name="grass",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )


@pytest.fixture
def mock_shoreline_state() -> ShorelineState:
    return ShorelineState(
        id="grassy-shore",
        name="shoreline-1",
        layer="0",
        position=Position(x=70, y=0),
        height=0,
        depth=0,
        orientation=Directions.LEFT.value,
        length=32,
        thickness=8,
        bidirectional=True,
        parent_fluid="jasilynns-tears",
        hitboxes=[
            Hitbox(Position(0, 0), Dimensions(32, 32))
        ]
    )


@pytest.fixture
def mock_positional_state() -> PositionalState:
    return PositionalState(
        id="wood-crate", 
        layer="0", 
        position=Position(x=10, y=10), 
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_positional_state_alt() -> PositionalState:
    return PositionalState(
        id="wood-raft",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_door_state() -> DoorState:
    return DoorState(
        id="door-front",
        layer="0",
        outlayer="brick-house-compose-layer",
        position=Position(x=100, y=100),
        out=Position(x=20, y=20)
    )


@pytest.fixture
def mock_switch_state() -> SwitchState:
    return SwitchState(
        id="castle-gate", 
        layer="0", 
        position=Position(x=70, y=80), 
        switch=True
    )


@pytest.fixture
def mock_motor_state() -> MotorState:
    return MotorState(
        id="arrow-1",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=50.0, vy=0.0)
    )


@pytest.fixture
def mock_fluid_state() -> FluidState:
    return FluidState(
        id="waterflow-1",
        name="jasilynns-tears",
        layer="0",
        position=Position(x=70, y=0),
        source=Directions.DOWN.value,
        flow=2,
        length=0,
        dirty=True
    )


@pytest.fixture
def mock_fluid_state_alt() -> FluidState:
    return FluidState(
        id="waterflow-1",
        layer="0",
        position=Position(x=200, y=100),
        source=Directions.LEFT.value,
        flow=1,
        length=100,
        hitboxes=[Hitbox(Position(-100, 0), Dimensions(100, 32))]
    )


@pytest.fixture
def mock_craft_states(
    mock_property_state,
    mock_property_state_alt,
    mock_property_state_alt2
) -> CraftStateInstances:
    return CraftStateInstances(
        struts = [
            mock_property_state,
            mock_property_state_alt,
            mock_property_state_alt2
        ]
    )


@pytest.fixture
def mock_sheet_states(
    mock_player_state,
    mock_sprite_state
) -> SheetStateInstances:
    return SheetStateInstances(
        players = [ mock_player_state ],
        sprites = [ mock_sprite_state ]
    )


@pytest.fixture
def mock_tile_states(
    mock_back_tile
) -> TileStateInstances:
    return TileStateInstances(
        back = [ mock_back_tile ]
    )


@pytest.fixture
def mock_object_states(
    mock_door_state
) -> ObjectStateInstances:
    return ObjectStateInstances(
        doors = [ mock_door_state ]
    )


@pytest.fixture
def mock_state(
    mock_sheet_states,
    mock_tile_states,
    mock_craft_states,
    mock_object_states
):
    return StateSchema(
        sheets = mock_sheet_states,
        tiles = mock_tile_states,
        crafts = mock_craft_states,
        objects = mock_object_states,
    )

