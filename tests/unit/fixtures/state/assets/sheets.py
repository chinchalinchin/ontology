"""
# Ontology: tests.unit.fixtures.state.sheets

Mock Sheet State Fixtures aligned with src/data/state/world-01/sheets/.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Intentions,
    Motivations,
    Goals,
    Relationships,
)
from app.models.state import (
    SheetStateInstances,
    SpriteState,
    SheetState,
    Inventory,
    Equipment,
    Mutators,
    MutatorParameters,
    RadialParameters,
    FearParameters,
    Character,
    Goal,
    Memory,
    Meter,
    Meters,
    Psyche,
)

# Cython Libraries
from libs.core.models import Position


@pytest.fixture
def mock_player_state() -> SheetState:
    return SheetState(
        id="player",
        name="player",
        layer="0",
        elevation=0,
        position=Position(x=5, y=80),
        meters=Meters(
            health=Meter(current=50, maximum=100),
            magic=Meter(current=100, maximum=100),
        ),
        character=Character(
            strength=5,
            defense=5,
            speed=100,
            impulse=25,
        ),
        mutators=Mutators(
            parameters=MutatorParameters(
                action=RadialParameters(radius=30),
            ),
        ),
        inventory=Inventory(
            pack=None,
            pouch=None,
            equipment=Equipment(
                armor=None,
                tool=None,
                utility=None,
                weapon="shortsword",
                shield="buckler",
            ),
            wallet=0,
        ),
    )


@pytest.fixture
def mock_sprite_state() -> SpriteState:
    player_goal = Goal(
        name="player",
        category=Goals.SUBJECT.value,
        layer="0",
        position=Position(x=100, y=200),
    )
    return SpriteState(
        id="jasilynn",
        name="evil-empress-jasilynn",
        layer="brick-house-compose-layer-1",
        elevation=0,
        position=Position(x=175, y=200),
        meters=Meters(
            health=Meter(current=50, maximum=100),
            magic=Meter(current=100, maximum=100),
        ),
        character=Character(
            strength=5,
            defense=5,
            speed=50,
            impulse=25,
        ),
        mutators=Mutators(
            parameters=MutatorParameters(
                fear=FearParameters(radius=100, limit=0.50, enemy=5),
                vision=RadialParameters(radius=150),
                action=RadialParameters(radius=25),
                squeeze=RadialParameters(radius=10),
            ),
        ),
        psyche=Psyche(
            dialogue="greeting",
            expression=None,
            motivation=Motivations.CONQUEST.value,
            persona="empress-jasilynn",
        ),
        intention=Intentions.FIND.value,
        goal=player_goal,
        memory=Memory(
            goals={"player": player_goal},
            prices=None,
            property=None,
            relationships={"player": Relationships.FRIEND.value},
            rumors=None,
            sprites={"player": Position(x=100, y=200)},
        ),
        inventory=Inventory(
            pouch=None,
            pack=None,
            equipment=Equipment(
                armor=None,
                tool=None,
                utility=None,
                weapon="shortsword",
                shield=None,
            ),
            wallet=0,
        ),
    )


@pytest.fixture
def mock_sheet_states(
    mock_player_state,
    mock_sprite_state,
) -> SheetStateInstances:
    return SheetStateInstances(
        players=[mock_player_state],
        sprites=[mock_sprite_state],
    )