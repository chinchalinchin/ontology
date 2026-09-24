"""
# Ontology: tests.unit.test_app_game_devices

Unit tests for input polling devices.
"""

from unittest.mock import patch
from app.config.enums import (
    DeviceContexts,
    Intentions,
    Directions,
    Interactions,
    Traversal,
    Menus
)
from app.game.devices import Keyboard, Controller
from app.models.config import (
    DeviceMapping,
    WorldMapping, 
    MenuMapping,
    MappingConfiguration

)
from app.models.state import DevicePayload


def test_keyboard_initialization(mock_keyboard: Keyboard):
    """
    Ensure the scancodes and initial state dictionaries are populated correctly.
    """

    expected_scancodes = {44, 8, 26, 22, 41}
    assert set(mock_keyboard._scancodes) == expected_scancodes
    
    # Ensure the initial state frame is populated with 0s
    assert all(state == 0 for state in mock_keyboard._last_state.values())
    assert len(mock_keyboard._last_state) == len(expected_scancodes)


def test_controller_initialization(mock_mapping_configuration: MappingConfiguration):
    """
    Ensure Controller instantiates and retains its mapping configuration.
    """
    controller = Controller(mock_mapping_configuration.controller)
    assert controller.mapping == mock_mapping_configuration.controller


def test_keyboard_handles_none_scancodes():
    """
    Ensure None values in mapping definitions are excluded from the active scancodes tuple.
    """
    mapping = DeviceMapping(
        world=WorldMapping(
            intentions={
                'attack': 44, 
                'interact': None
            },
            goals={
                'up': 26, 
                'down': None
            },
            menus={
                'pause': None
            }
        ),
        menu=MenuMapping()
    )
    keyboard = Keyboard(mapping)
    assert set(keyboard._scancodes) == {44, 26}


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_polling_return_type_and_mappings(
    mock_poll, 
    mock_pump, 
    mock_keyboard: Keyboard
):
    """
    Ensure the poll method correctly formats the returned dict with active scancodes.
    """
    
    # Simulate 'up' (26) and 'interact' (8) being pressed
    pressed_codes = {26, 8}
    mock_poll.return_value = tuple(
        1 if code in pressed_codes else 0 for code in mock_keyboard._scancodes
    )
    
    result = mock_keyboard.poll()
    
    assert mock_pump.called
    assert mock_poll.called
    assert isinstance(result, DevicePayload)
    
    assert Directions.UP.value in result.world.goals
    assert len(result.world.goals) == 1
    assert result.world.intention == Intentions.INTERACT.value


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_edge_triggered_intentions(
    mock_poll, 
    mock_pump, 
    mock_keyboard: Keyboard
):
    """
    Ensure Intentions only trigger on the rising edge (0 -> 1) of the keypress.
    """    
    # Frame 1: Press 'attack' (44)
    mock_poll.return_value = tuple(
        1 if code == 44 else 0 for code in mock_keyboard._scancodes
    )
    result_frame_1 = mock_keyboard.poll()
    assert result_frame_1.world.intention == Intentions.ATTACK.value
    
    # Frame 2: Hold 'attack' (44)
    mock_poll.return_value = tuple(
        1 if code == 44 else 0 for code in mock_keyboard._scancodes
    )
    result_frame_2 = mock_keyboard.poll()
    assert result_frame_2.world.intention != Intentions.ATTACK.value
    
    # Frame 3: Release 'attack' (44)
    mock_poll.return_value = tuple(
        0 for _ in mock_keyboard._scancodes
    )
    result_frame_3 = mock_keyboard.poll()
    assert result_frame_3.world.intention != Intentions.ATTACK.value
    
    # Frame 4: Press 'attack' (44) again
    mock_poll.return_value = tuple(
        1 if code == 44 else 0 for code in mock_keyboard._scancodes
    )
    result_frame_4 = mock_keyboard.poll()
    assert result_frame_4.world.intention == Intentions.ATTACK.values


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_level_triggered_goals(
    mock_poll,
    mock_pump, 
    mock_keyboard
):
    """
    Ensure Goals trigger continuously (level-triggered) while the key is held.
    """
    
    # Frame 1: Press 'down' (22)
    mock_poll.return_value = tuple(
        1 if code == 22 else 0 for code in mock_keyboard._scancodes
    )
    result_frame_1 = mock_keyboard.poll()
    assert Directions.DOWN.value in result_frame_1.world.goals
    
    # Frame 2: Hold 'down' (22)
    mock_poll.return_value = tuple(
        1 if code == 22 else 0 for code in mock_keyboard._scancodes
    )
    result_frame_2 = mock_keyboard.poll()
    assert Directions.DOWN.value in result_frame_2.world.goals
    
    # Frame 3: Release 'down' (22)
    mock_poll.return_value = tuple(
        0 for _ in mock_keyboard._scancodes
    )
    result_frame_3 = mock_keyboard.poll()
    assert Directions.DOWN.value not in result_frame_3.world.goals


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_multiple_goals_accumulation(
    mock_poll, 
    mock_pump, 
    mock_keyboard
):
    """
    Ensure multiple simultaneously pressed directional keys accumulate into world.goals.
    """    
    # Simulate 'up' (26) and 'down' (22) pressed simultaneously
    pressed_codes = {26, 22}
    mock_poll.return_value = tuple(
        1 if code in pressed_codes else 0 for code in mock_keyboard._scancodes
    )
    result = mock_keyboard.poll()
    
    assert set(result.world.goals) == {
        Directions.UP.value, 
        Directions.DOWN.value
    }


def test_keyboard_context_switching(mock_keyboard: Keyboard):
    """
    Ensure switching contexts recalculates scancodes and resets tracking state.
    """
    # World Context
    expected_world_codes = {44, 8, 26, 22, 41}
    assert set(mock_keyboard._scancodes) == expected_world_codes
    assert mock_keyboard._context == DeviceContexts.WORLD.value

    # Switch to Menu Context
    mock_keyboard.context(DeviceContexts.MENU.value)
    expected_menu_codes = {79, 80, 40, 41}
    assert set(mock_keyboard._scancodes) == expected_menu_codes
    assert mock_keyboard._context == DeviceContexts.MENU.value

    # Guard clause: Re-invoking the same context preserves the state buffer
    mock_keyboard._last_state[79] = 1
    mock_keyboard.context(DeviceContexts.MENU.value)
    assert mock_keyboard._last_state[79] == 1


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_menu_polling_edge_triggered(
    mock_poll, 
    mock_pump, 
    mock_keyboard: Keyboard
):
    """
    Ensure Traversal and Interaction inputs in MENU context trigger only on rising edges.
    """
    mock_keyboard.context(DeviceContexts.MENU.value)

    # Frame 1: Press 'north' (79) and 'select' (40)
    mock_poll.return_value = tuple(
        1 if code in {79, 40} else 0 for code in mock_keyboard._scancodes
    )
    payload_1 = mock_keyboard.poll()
    assert payload_1.menu.traversal == Traversal.NORTH.value
    assert payload_1.menu.interaction == Interactions.SELECT.value
    assert payload_1.world.intention is None

    # Frame 2: Hold 'north' (79) and 'select' (40)
    mock_poll.return_value = tuple(
        1 if code in {79, 40} else 0 for code in mock_keyboard._scancodes
    )
    payload_2 = mock_keyboard.poll()
    assert payload_2.menu.traversal is None
    assert payload_2.menu.interaction is None

    # Frame 3: Release all keys
    mock_poll.return_value = tuple(
        0 for _ in mock_keyboard._scancodes
    )
    payload_3 = mock_keyboard.poll()
    assert payload_3.menu.traversal is None
    assert payload_3.menu.interaction is None

    # Frame 4: Press 'cancel' (41)
    mock_poll.return_value = tuple(
        1 if code == 41 else 0 for code in mock_keyboard._scancodes
    )
    payload_4 = mock_keyboard.poll()
    assert payload_4.menu.interaction == Interactions.CANCEL.value


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_world_menu_trigger(
    mock_poll, 
    mock_pump, 
    mock_keyboard: Keyboard
):
    """
    Ensure opening a menu while in WORLD context is edge-triggered.
    """

    # Frame 1: Press 'pause' (41)
    mock_poll.return_value = tuple(
        1 if code == 41 else 0 for code in mock_keyboard._scancodes
    )
    payload = mock_keyboard.poll()
    assert payload.world.menu == 'pause'

    # Frame 2: Hold 'pause' (41)
    mock_poll.return_value = tuple(
        1 if code == 41 else 0 for code in mock_keyboard._scancodes
    )
    payload_held = mock_keyboard.poll()
    assert payload_held.world.menu is None