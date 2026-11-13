"""
@domain.test
@test.unit
@app.device
@workflow.player

# Ontology: Tests - tests.unit.app.game.test_devices

Unit tests for Device classes.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.devices import (
    Controller,
    Keyboard,
)
from app.models.state import DevicePayload
from app.static.semantics import (
    DeviceContexts,
    Devices,
    Directions,
    Hands,
    Intentions,
    Interactions,
    Menus,
    Traversal,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_device,
    pytest.mark.workflow_player,
]

# -----------------------------------------------------

EXPECTED_WORLD_SCANCODES = {
    4, 5, 6, 7, 8, 9, 20, 22, 26, 30, 31, 32, 33, 34, 44, 224, 225, 226
}
EXPECTED_MENU_SCANCODES = {4, 7, 22, 26, 43, 44}


def test_keyboard_initialization(mock_keyboard: Keyboard):
    """
    Ensure the scancodes and initial state dictionaries are populated from main.yaml.
    """
    assert set(mock_keyboard._scancodes) == EXPECTED_WORLD_SCANCODES
    assert all(state == 0 for state in mock_keyboard._last_state.values())
    assert len(mock_keyboard._last_state) == len(EXPECTED_WORLD_SCANCODES)


def test_controller_initialization(mock_device, mock_configurations_schema):
    """
    Ensure Controller instantiates via mock_device and retains its mapping configuration.
    """
    controller = mock_device(Devices.CONTROLLER.value)
    assert isinstance(controller, Controller)
    assert controller.mapping == mock_configurations_schema.mappings.controller


def test_keyboard_handles_none_scancodes(mock_keyboard: Keyboard, mock_sdl):
    """
    Ensure None values in mapping definitions are excluded from active scancodes and polling.
    """
    mock_keyboard.mapping.world.intentions[Intentions.SPRINT.value] = None
    mock_keyboard.mapping.world.menus[Menus.TRADE.value] = None
    mock_keyboard._context = None
    mock_keyboard.context(DeviceContexts.WORLD.value)

    assert 224 not in mock_keyboard._scancodes
    assert 34 not in mock_keyboard._scancodes
    assert None not in mock_keyboard._scancodes

    mock_sdl({44})
    payload = mock_keyboard.poll()
    assert payload.world.intention == Intentions.ATTACK.value


def test_keyboard_polling_return_type_and_mappings(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure the poll method resolves active world goals and intentions into a DevicePayload.
    """
    # Simulate 'up' (26) and 'interact' (8) being pressed
    mock_sdl({26, 8})
    result = mock_keyboard.poll()

    assert isinstance(result, DevicePayload)
    assert result.world.goals == [Directions.UP.value]
    assert result.world.intention == Intentions.INTERACT.value


def test_keyboard_edge_triggered_intentions(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure Intentions only trigger on the rising edge (0 -> 1) of the keypress.
    """
    # Frame 1: Press 'attack' (44)
    mock_sdl({44})
    result_frame_1 = mock_keyboard.poll()
    assert result_frame_1.world.intention == Intentions.ATTACK.value

    # Frame 2: Hold 'attack' (44)
    mock_sdl({44})
    result_frame_2 = mock_keyboard.poll()
    assert result_frame_2.world.intention is None

    # Frame 3: Release 'attack' (44)
    mock_sdl(set())
    result_frame_3 = mock_keyboard.poll()
    assert result_frame_3.world.intention is None

    # Frame 4: Press 'attack' (44) again
    mock_sdl({44})
    result_frame_4 = mock_keyboard.poll()
    assert result_frame_4.world.intention == Intentions.ATTACK.value


@pytest.mark.modality_intention
def test_keyboard_edge_triggered_grips_resolve_use_intention(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure left (20) and right (9) grip keys resolve world.grip and default world.intention to USE.
    """
    # Frame 1: Press 'left' grip (20)
    mock_sdl({20})
    p1 = mock_keyboard.poll()
    assert p1.world.grip == Hands.LEFT.value
    assert p1.world.intention == Intentions.USE.value

    # Frame 2: Hold 'left' grip (20) -> edge-triggered, does not re-fire
    mock_sdl({20})
    p2 = mock_keyboard.poll()
    assert p2.world.grip is None
    assert p2.world.intention is None

    # Frame 3: Press 'right' grip (9)
    mock_sdl({9})
    p3 = mock_keyboard.poll()
    assert p3.world.grip == Hands.RIGHT.value
    assert p3.world.intention == Intentions.USE.value


@pytest.mark.workflow_inventory
@pytest.mark.parametrize(
    "scancode, expected_menu",
    [
        (31, Menus.EQUIPMENT.value),
        (32, Menus.POUCH.value),
        (33, Menus.PACK.value),
    ],
)
def test_keyboard_inventory_menu_triggers(
    mock_keyboard: Keyboard,
    mock_sdl,
    scancode: int,
    expected_menu: str,
):
    """
    Ensure dedicated scancodes trigger Equipment, Pouch, and Pack menus in WORLD context.
    """
    mock_sdl({scancode})
    payload = mock_keyboard.poll()
    assert payload.world.menu == expected_menu


def test_keyboard_level_triggered_goals(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure Goals trigger continuously (level-triggered) while the key is held.
    """
    # Frame 1: Press 'down' (22)
    mock_sdl({22})
    result_frame_1 = mock_keyboard.poll()
    assert Directions.DOWN.value in result_frame_1.world.goals

    # Frame 2: Hold 'down' (22)
    mock_sdl({22})
    result_frame_2 = mock_keyboard.poll()
    assert Directions.DOWN.value in result_frame_2.world.goals

    # Frame 3: Release 'down' (22)
    mock_sdl(set())
    result_frame_3 = mock_keyboard.poll()
    assert Directions.DOWN.value not in result_frame_3.world.goals


def test_keyboard_multiple_goals_accumulation(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure multiple simultaneously pressed directional keys accumulate into world.goals.
    """
    # Simulate 'up' (26) and 'right' (7) pressed simultaneously
    mock_sdl({26, 7})
    result = mock_keyboard.poll()

    assert set(result.world.goals) == {
        Directions.UP.value,
        Directions.RIGHT.value,
    }


def test_keyboard_context_switching(mock_keyboard: Keyboard):
    """
    Ensure switching contexts recalculates scancodes and resets tracking state.
    """
    # World Context
    assert set(mock_keyboard._scancodes) == EXPECTED_WORLD_SCANCODES
    assert mock_keyboard._context == DeviceContexts.WORLD.value

    # Switch to Menu Context
    mock_keyboard.context(DeviceContexts.MENU.value)
    assert set(mock_keyboard._scancodes) == EXPECTED_MENU_SCANCODES
    assert mock_keyboard._context == DeviceContexts.MENU.value

    # Guard clause: Re-invoking the same context preserves the state buffer
    mock_keyboard._last_state[26] = 1
    mock_keyboard.context(DeviceContexts.MENU.value)
    assert mock_keyboard._last_state[26] == 1


def test_keyboard_menu_polling_edge_triggered(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure Traversal and Interaction inputs in MENU context trigger only on rising edges.
    """
    mock_keyboard.context(DeviceContexts.MENU.value)

    # Frame 1: Press 'north' (26) and 'select' (44)
    mock_sdl({26, 44})
    payload_1 = mock_keyboard.poll()
    assert payload_1.menu.traversal == Traversal.NORTH.value
    assert payload_1.menu.interaction == Interactions.SELECT.value
    assert payload_1.world.intention is None

    # Frame 2: Hold 'north' (26) and 'select' (44)
    mock_sdl({26, 44})
    payload_2 = mock_keyboard.poll()
    assert payload_2.menu.traversal is None
    assert payload_2.menu.interaction is None

    # Frame 3: Release all keys
    mock_sdl(set())
    payload_3 = mock_keyboard.poll()
    assert payload_3.menu.traversal is None
    assert payload_3.menu.interaction is None

    # Frame 4: Press 'cancel' (43)
    mock_sdl({43})
    payload_4 = mock_keyboard.poll()
    assert payload_4.menu.interaction == Interactions.CANCEL.value


def test_keyboard_world_menu_trigger(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure opening a menu while in WORLD context is edge-triggered.
    """
    # Frame 1: Press 'pause' (30)
    mock_sdl({30})
    payload = mock_keyboard.poll()
    assert payload.world.menu == Menus.PAUSE.value

    # Frame 2: Hold 'pause' (30)
    mock_sdl({30})
    payload_held = mock_keyboard.poll()
    assert payload_held.world.menu is None


def test_keyboard_singular_resolution_priority(
    mock_keyboard: Keyboard,
    mock_sdl,
):
    """
    Ensure overlapping edge-triggered inputs collapse to the first configured key.
    """
    # Simultaneously press 'interact' (8) and 'attack' (44), plus 'pause' (30) and 'equipment' (31)
    mock_sdl({8, 44, 30, 31})
    world_payload = mock_keyboard.poll()
    assert world_payload.world.intention == Intentions.INTERACT.value
    assert world_payload.world.menu == Menus.PAUSE.value

    # Switch to MENU and press 'north' (26) and 'south' (22), plus 'select' (44) and 'cancel' (43)
    mock_keyboard.context(DeviceContexts.MENU.value)
    mock_sdl({26, 22, 44, 43})
    menu_payload = mock_keyboard.poll()
    assert menu_payload.menu.traversal == Traversal.NORTH.value
    assert menu_payload.menu.interaction == Interactions.SELECT.value