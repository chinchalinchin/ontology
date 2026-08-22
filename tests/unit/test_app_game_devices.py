"""
# Ontology: tests.unit.test_app_game_devices

Unit tests for input polling devices.
"""

import pytest
from unittest.mock import patch
from app.game.devices import Keyboard
from app.models.config import Mapping

@pytest.fixture
def keyboard_mapping() -> Mapping:
    """
    Provides a mock input mapping configuration.
    """
    return Mapping(
        intentions={'attack': 44, 'interact': 8},
        goals={'up': 26, 'down': 22}
    )

def test_keyboard_initialization(keyboard_mapping: Mapping):
    """
    Ensure the scancodes and initial state dictionaries are populated correctly.
    """
    keyboard = Keyboard(keyboard_mapping)
    
    expected_scancodes = {44, 8, 26, 22}
    assert set(keyboard._scancodes) == expected_scancodes
    
    # Ensure the initial state frame is populated with 0s
    assert all(state == 0 for state in keyboard._last_state.values())
    assert len(keyboard._last_state) == len(expected_scancodes)


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_polling_return_type_and_mappings(mock_poll, mock_pump, keyboard_mapping: Mapping):
    """
    Ensure the poll method correctly formats the returned Mapping with active scancodes.
    """
    keyboard = Keyboard(keyboard_mapping)
    
    # Simulate 'up' (26) and 'interact' (8) being pressed
    pressed_codes = {26, 8}
    mock_poll.return_value = tuple(1 if code in pressed_codes else 0 for code in keyboard._scancodes)
    
    result = keyboard.poll()
    
    assert mock_pump.called
    assert mock_poll.called
    assert isinstance(result, Mapping)
    
    assert 'up' in result.goals
    assert len(result.goals) == 1
    
    assert 'interact' in result.intentions
    assert len(result.intentions) == 1


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_edge_triggered_intentions(mock_poll, mock_pump, keyboard_mapping: Mapping):
    """
    Ensure Intentions only trigger on the rising edge (0 -> 1) of the keypress.
    """
    keyboard = Keyboard(keyboard_mapping)
    
    # Frame 1: Press 'attack' (44)
    mock_poll.return_value = tuple(1 if code == 44 else 0 for code in keyboard._scancodes)
    result_frame_1 = keyboard.poll()
    assert 'attack' in result_frame_1.intentions
    
    # Frame 2: Hold 'attack' (44)
    mock_poll.return_value = tuple(1 if code == 44 else 0 for code in keyboard._scancodes)
    result_frame_2 = keyboard.poll()
    assert 'attack' not in result_frame_2.intentions
    
    # Frame 3: Release 'attack' (44)
    mock_poll.return_value = tuple(0 for _ in keyboard._scancodes)
    result_frame_3 = keyboard.poll()
    assert 'attack' not in result_frame_3.intentions
    
    # Frame 4: Press 'attack' (44) again
    mock_poll.return_value = tuple(1 if code == 44 else 0 for code in keyboard._scancodes)
    result_frame_4 = keyboard.poll()
    assert 'attack' in result_frame_4.intentions


@patch('app.game.devices.sdl.pump')
@patch('app.game.devices.sdl.poll')
def test_keyboard_level_triggered_goals(mock_poll, mock_pump, keyboard_mapping: Mapping):
    """
    Ensure Goals trigger continuously (level-triggered) while the key is held.
    """
    keyboard = Keyboard(keyboard_mapping)
    
    # Frame 1: Press 'down' (22)
    mock_poll.return_value = tuple(1 if code == 22 else 0 for code in keyboard._scancodes)
    result_frame_1 = keyboard.poll()
    assert 'down' in result_frame_1.goals
    
    # Frame 2: Hold 'down' (22)
    mock_poll.return_value = tuple(1 if code == 22 else 0 for code in keyboard._scancodes)
    result_frame_2 = keyboard.poll()
    assert 'down' in result_frame_2.goals
    
    # Frame 3: Release 'down' (22)
    mock_poll.return_value = tuple(0 for _ in keyboard._scancodes)
    result_frame_3 = keyboard.poll()
    assert 'down' not in result_frame_3.goals