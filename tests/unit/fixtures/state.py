"""
# Ontology: tests.unit.fixtures.state

Mock Asset State Fixtures
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
    PlotState,
    ContainerState,
    ReactableState,
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
def mock_plot_state() -> PlotState:
    return PlotState(
        current="town-locked",
        previous=[]
    )

# ------------------------------------------------------------ CRAFT STATES

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

# ------------------------------------------------------------ OBJECT STATES

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
    """
    Raft positional state initialized to an idle coordinate clear of fluid corridors.
    """
    return PositionalState(
        id="wood-raft",
        layer="0",
        position=Position(x=10, y=200),
        velocity=Velocity(vx=0.0, vy=0.0)
    )


@pytest.fixture
def mock_positional_state_alt2() -> PositionalState:
    """
    Upstream crate positional state positioned along the fluid x=70 axis.
    """
    return PositionalState(
        id="wood-crate",
        layer="0",
        position=Position(x=70, y=10),
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
        position=Position(x=170, y=180), 
        switch=True
    )


@pytest.fixture
def mock_switch_state_alt() -> SwitchState:
    return SwitchState(
        id="pressure-plate",
        layer="0",
        depth=0,
        height=None,
        position=Position(x=30, y=30),
        switch=False,
        link="castle-gate"
    )

@pytest.fixture
def mock_container_state() -> ContainerState:
    return ContainerState(
        id="wood-chest",
        layer="0",
        depth=0,
        height=None,
        position=Position(x=100, y=100),
        switch=False,
        content=["gold-coin"]
    )


# ------------------------------------------------------------ SPRITE STATES

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


# ------------------------------------------------------------ TILE STATES

@pytest.fixture
def mock_multiplier_state() -> MultiplierState:
    return MultiplierState(
        id="tile-1",
        name="grass",
        layer="0",
        position=Position(x=0, y=0),
        multiple=Multiple(nx=10, ny=10)
    )


# -------------------------------------------------------- GEOGRAPHY STATES

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

# ------------------------------------------------------- PROJECTILE STATES

@pytest.fixture
def mock_motor_state() -> MotorState:
    return MotorState(
        id="arrow-1",
        layer="0",
        position=Position(x=70, y=50),
        velocity=Velocity(vx=50.0, vy=0.0)
    )

# ---------------------------------------------------------- EFFECT STATES

@pytest.fixture
def mock_fluid_state() -> FluidState:
    return FluidState(
        id="waterflow-01",
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
        id="waterflow-01",
        name="jasilynns-tears-alt",
        layer="0",
        position=Position(x=200, y=100),
        source=Directions.LEFT.value,
        flow=1,
        length=100,
        hitboxes=[Hitbox(Position(-100, 0), Dimensions(100, 32))]
    )


@pytest.fixture
def mock_fluid_state_alt2() -> FluidState:
    """
    Secondary fluid emitter state adjacent to fluid-1's East flank.
    """
    return FluidState(
        id="waterflow-01",
        name="fluid-adjacent",
        layer="0",
        position=Position(x=102, y=0),
        source=Directions.DOWN.value,
        flow=1,
        length=320,
        dirty=True
    )

@pytest.fixture
def mock_reactable_state() -> ReactableState:
    return ReactableState(
        id="reactable-1",
        layer="0",
        depth=0,
        height=None,
        position=Position(x=200, y=200),
        animation=AnimationState(),
        intention=Intentions.ATTACK.value,
        active=True
    )

# ---------------------------------------------------------- STATE SCHEMAS

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
def mock_effect_states(
    mock_reactable_state,
    mock_fluid_state,
    mock_fluid_state_alt,
    mock_fluid_state_alt2
) -> EffectStateInstances:
    return EffectStateInstances(
        reactables = [ mock_reactable_state ],
        fluids = [ mock_fluid_state, mock_fluid_state_alt, mock_fluid_state_alt2 ],
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
    mock_multiplier_state
) -> TileStateInstances:
    return TileStateInstances(
        back = [ mock_multiplier_state ]
    )


@pytest.fixture
def mock_object_states(
    mock_door_state,
    mock_container_state,
    mock_switch_state,
    mock_switch_state_alt
) -> ObjectStateInstances:
    return ObjectStateInstances(
        doors = [ mock_door_state ],
        chests = [ mock_container_state ],
        plates = [ mock_switch_state_alt ],
        gates = [ mock_switch_state ]
    )

# ---------------------------------------------------------------------------------

@pytest.fixture
def mock_state(
    mock_sheet_states,
    mock_tile_states,
    mock_craft_states,
    mock_object_states,
    mock_effect_states
):
    return StateSchema(
        effects = mock_effect_states,
        sheets = mock_sheet_states,
        tiles = mock_tile_states,
        crafts = mock_craft_states,
        objects = mock_object_states,
    )

