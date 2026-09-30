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
    Goals,
)
from app.models.state import (
    # -------- MODELS
    SpriteState,
    PlayerState,
    AnimationState,
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
    Position,
    Velocity,
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

