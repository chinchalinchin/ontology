"""
@domain.test
@test.unit
@app.mechanic
@physics.space
@category.sheets
@category.objects
@modality.intention
@workflow.interactions

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_interaction

Unit tests for InteractionMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Intentions,
    Mechanics,
    Menus,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.physics_space,
    pytest.mark.modality_intention,
    pytest.mark.workflow_interactions,
]

# -----------------------------------------------------


def test_interaction_sprite_door_relayers_and_memorizes(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.INTERACTION.value)
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]
    sprite = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    door_hb = door.hitboxes[0]
    sprite_hb = sprite.hitboxes[0]
    sprite.state.position = Position(
        door.state.position.x + door_hb.position.x - sprite_hb.position.x,
        door.state.position.y + door_hb.position.y - sprite_hb.position.y,
    )
    sprite.state.intention = Intentions.INTERACT.value
    sprite.state.memory.doors.clear()

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert sprite.state.layer == door.state.outlayer
    assert sprite.state.position.x == door.state.out.x
    assert sprite.state.position.y == door.state.out.y
    assert sprite.state.memory.doors[door.name] == door.state.outlayer


def test_interaction_player_door_resets_intention(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.INTERACTION.value)
    door = mock_board.instances(AssetInstances.DOORS.value, "0")[0]
    player = mock_board.player()

    door_hb = door.hitboxes[0]
    player_hb = player.hitboxes[0]
    player.state.position = Position(
        door.state.position.x + door_hb.position.x - player_hb.position.x,
        door.state.position.y + door_hb.position.y - player_hb.position.y,
    )
    player.state.intention = Intentions.INTERACT.value

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert player.state.layer == door.state.outlayer
    assert player.state.intention == Intentions.IDLE.value


def test_interaction_player_sign_emits_text_menu(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.INTERACTION.value)
    sign = mock_board.instances(AssetInstances.SIGNS.value, "0")[0]
    player = mock_board.player()

    sign_hb = sign.hitboxes[0]
    player_hb = player.hitboxes[0]
    player.state.position = Position(
        sign.state.position.x + sign_hb.position.x - player_hb.position.x,
        sign.state.position.y + sign_hb.position.y - player_hb.position.y,
    )
    player.state.intention = Intentions.INTERACT.value

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert len(mock_bus) == 1
    assert mock_bus[0].id == Menus.TEXT.value