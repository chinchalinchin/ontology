"""
@domain.test
@test.unit
@app.mechanic
@modality.intention
@workflow.player

# Ontology: Tests - tests.unit.app.game.logic.mechanics.intentional.test_player

Unit tests for PlayerMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Actions,
    Directions,
    Intentions,
    Mechanics,
    Menus,
    PlayerGoals,
)
from app.models.state import (
    DevicePayload,
    MenuPayload,
    WorldPayload,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.modality_intention,
    pytest.mark.workflow_player,
]

# -----------------------------------------------------


def test_player_new_intention_resets_animation(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PLAYER.value)
    player = mock_board.player()
    player.state.intention = Intentions.IDLE.value
    player.state.animation.frame = 5
    player.state.animation.tick = 3

    payload = mock_payload(intention=Intentions.MINE.value)
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.intention == Intentions.MINE.value
    assert player.state.animation.frame == 0
    assert player.state.animation.tick == 0
    assert player.state.animation.action == Actions.THRUST.value
    assert player.state.mutators.triggers.animated is True


def test_player_blocking_intention_persists(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PLAYER.value)
    player = mock_board.player()
    player.state.intention = Intentions.MINE.value
    player.state.animation.frame = 1
    player.state.animation.tick = 0

    payload = mock_payload(intention=None, goals=[])
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.intention == Intentions.MINE.value


def test_player_blocking_intention_completes(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PLAYER.value)
    player = mock_board.player()
    player.state.intention = Intentions.MINE.value
    player.state.animation.frame = 0
    player.state.animation.tick = 0

    payload = mock_payload(intention=None, goals=[])
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.intention == Intentions.IDLE
    assert player.state.mutators.triggers.animated is False


def test_player_movement_updates_goal(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PLAYER.value)
    player = mock_board.player()
    player.state.position.x = 100
    player.state.position.y = 100
    player.state.goal = None
    speed = player.state.character.speed

    payload = mock_payload(
        intention=None,
        goals=[PlayerGoals.RIGHT, PlayerGoals.DOWN],
    )
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.goal is not None
    assert player.state.goal.position.x == 100 + speed
    assert player.state.goal.position.y == 100 + speed
    assert player.state.mutators.triggers.animated is True


def test_player_movement_cardinal_directions(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PLAYER.value)
    player = mock_board.player()
    player.state.position.x = 100
    player.state.position.y = 100

    mechanic.update(
        mock_board,
        0.016,
        mock_bus,
        mock_payload(goals=[PlayerGoals.UP]),
    )
    assert player.state.animation.direction == Directions.UP.value

    mechanic.update(
        mock_board,
        0.016,
        mock_bus,
        mock_payload(goals=[PlayerGoals.LEFT]),
    )
    assert player.state.animation.direction == Directions.LEFT.value


def test_player_menu_triggers_emit_events(
    mock_mechanic,
    mock_board,
    mock_bus,
):
    mechanic = mock_mechanic(Mechanics.PLAYER.value)

    inv_payload = DevicePayload(
        world=WorldPayload(menu=Menus.INVENTORY.value),
        menu=MenuPayload(),
    )
    mechanic.update(mock_board, 0.016, mock_bus, inv_payload)
    assert len(mock_bus) == 1
    assert mock_bus[-1].id == Menus.INVENTORY.value

    pause_payload = DevicePayload(
        world=WorldPayload(menu=Menus.PAUSE.value),
        menu=MenuPayload(),
    )
    mechanic.update(mock_board, 0.016, mock_bus, pause_payload)
    assert len(mock_bus) == 2
    assert mock_bus[-1].id == Menus.PAUSE.value