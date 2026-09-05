"""
# Ontology: tests.unit.test_app_game_logic_mechanics_spatial_interaction
"""
import pytest
import collections
from unittest.mock import MagicMock, patch

from app.game.logic.mechanics.spatial.interaction import InteractionMechanics
from app.config.enums import Intentions, AssetInstances, AssetCategories, Menus
from app.game.menus.events import MenuEvent
from app.models.state import DevicePayload, ContainerState, DoorState, DialogueState
from libs.core.models import Position, Dimensions


@pytest.fixture
def interaction_mechanics():
    return InteractionMechanics()


def test_interaction_with_door_relayers_source(interaction_mechanics, mock_board):
    player = mock_board.player()
    player.state.intention = Intentions.INTERACT.value
    player.state.position = Position(x=10, y=10)
    
    door = MagicMock()
    door.name = "door-1"
    door.category = AssetCategories.OBJECTS.value
    door.instance = AssetInstances.DOORS.value
    door.taxonomy.instance = AssetInstances.DOORS.value
    door.properties.mass = 0
    door.state = DoorState(
        id="door-1",
        layer="0",
        position=Position(x=10, y=10),
        outlayer="1",
        out=Position(x=100, y=100)
    )
    door.dimensions = Dimensions(w=32, l=32)
    
    mock_board.add([door])
    bus = collections.deque()
    payload = MagicMock(spec=DevicePayload)
    
    # Force collision bypass for deterministic testing
    with patch.object(InteractionMechanics, 'collisions', return_value=[(player, door)]), \
         patch.object(InteractionMechanics, 'center', return_value=(15, 15)):
        
        interaction_mechanics.update(mock_board, 1.0, bus, payload)
        
        assert player.state.layer == "1"
        assert player.state.position.x == 100
        assert player.state.position.y == 100


def test_interaction_with_chest_transfers_loot_to_sprite(interaction_mechanics, mock_board):
    sprite = mock_board.assets()[0] 
    sprite.state.intention = Intentions.INTERACT.value
    sprite.state.position = Position(x=10, y=10)
    sprite.state.inventory.loot = {"gold": 5}
    
    chest = MagicMock()
    chest.name = "chest-1"
    chest.category = AssetCategories.OBJECTS.value
    chest.instance = AssetInstances.CHESTS.value
    chest.taxonomy.instance = AssetInstances.CHESTS.value
    chest.properties.mass = 0
    chest.state = ContainerState(
        id="chest-1",
        layer="0",
        position=Position(x=10, y=10),
        content=["ruby", "ruby"]
    )
    chest.dimensions = Dimensions(w=32, l=32)
    
    mock_board.add([chest])
    bus = collections.deque()
    payload = MagicMock(spec=DevicePayload)
    
    with patch.object(InteractionMechanics, 'collisions', return_value=[(sprite, chest)]), \
         patch.object(InteractionMechanics, 'center', return_value=(15, 15)):
        
        interaction_mechanics.update(mock_board, 1.0, bus, payload)
        
        assert sprite.state.inventory.loot.get("ruby") == 2
        assert sprite.state.inventory.loot.get("gold") == 5
        assert len(chest.state.content) == 0


def test_interaction_with_sign_dispatches_menu_event(interaction_mechanics, mock_board):
    player = mock_board.player()
    player.state.intention = Intentions.INTERACT.value
    player.state.position = Position(x=10, y=10)
    
    # Provide dummy plot state to satisfy context extraction
    mock_board.plot = MagicMock()
    mock_board.plot.current = "tutorial"
    
    sign = MagicMock()
    sign.name = "sign-1"
    sign.category = AssetCategories.OBJECTS.value
    sign.instance = AssetInstances.SIGNS.value
    sign.taxonomy.instance = AssetInstances.SIGNS.value
    sign.properties.mass = 0
    sign.state = DialogueState(
        id="sign-1",
        layer="0",
        position=Position(x=10, y=10),
        persona="narrator",
        lexicon="welcome_msg"
    )
    sign.dimensions = Dimensions(w=32, l=32)
    
    mock_board.add([sign])
    bus = collections.deque()
    payload = MagicMock(spec=DevicePayload)
    
    with patch.object(InteractionMechanics, 'collisions', return_value=[(player, sign)]), \
         patch.object(InteractionMechanics, 'center', return_value=(15, 15)):
        
        interaction_mechanics.update(mock_board, 1.0, bus, payload)
        
        assert len(bus) == 1
        event = bus.popleft()
        
        assert isinstance(event, MenuEvent)
        assert event.id == Menus.TEXT.value
        assert event.context['plot'] == "tutorial"
        assert event.context['persona'] == "narrator"
        assert event.context['lexicon'] == "welcome_msg"


def test_interaction_ignores_non_intersecting_centers(interaction_mechanics, mock_board):
    player = mock_board.player()
    player.state.intention = Intentions.INTERACT.value
    
    door = MagicMock()
    door.category = AssetCategories.OBJECTS.value
    door.instance = AssetInstances.DOORS.value
    door.taxonomy.instance = AssetInstances.DOORS.value
    door.properties.mass = 0
    door.state = DoorState(id="door-1", layer="0", position=Position(x=100, y=100), outlayer="1", out=Position(x=0, y=0))
    door.dimensions = Dimensions(w=32, l=32)
    
    mock_board.add([door])
    bus = collections.deque()
    
    with patch.object(InteractionMechanics, 'collisions', return_value=[(player, door)]), \
         patch.object(InteractionMechanics, 'center', return_value=(0, 0)): # Center is outside the target's bounds
        
        interaction_mechanics.update(mock_board, 1.0, bus, MagicMock())
        
        # Assert player layer did not change due to failed intersection check
        assert player.state.layer == "0"