"""
@domain.test
@test.unit
@app.mechanic
@category.sheets
@physics.space
@modality.intention

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_social

Unit tests for SocialMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Expressions,
    Goals,
    Intentions,
    Mechanics,
    Menus,
)
from app.models.state import Goal

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.physics_space,
    pytest.mark.modality_intention,
]

# -----------------------------------------------------


def test_social_player_npc_dialogue_interaction(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.SOCIAL.value)
    player = mock_board.player()
    npc = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    player.state.position = Position(100, 100)
    player.state.intention = Intentions.INTERACT.value
    npc.state.position = Position(105, 105)
    npc.state.psyche.dialogue = "greeting"

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert len(mock_bus) == 1
    assert mock_bus[0].id == Menus.DIALOGUE.value
    assert player.state.intention == Intentions.IDLE.value


def test_social_npc_to_npc_rumor_passing_and_expression(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.SOCIAL.value)
    sprites = mock_board.instances(AssetInstances.SPRITES.value, "0")
    speaker, listener = sprites[0], sprites[1]

    speaker.state.intention = Intentions.SPEAK.value
    speaker.state.psyche.dialogue = "secret-rumor"
    speaker.state.psyche.expression = None
    speaker.state.goal = Goal(
        name=listener.name,
        category=Goals.SUBJECT.value,
        layer="0",
        position=listener.state.position,
    )
    listener.state.memory.rumors.clear()

    mechanic.update(mock_board, 0.016, mock_bus, mock_payload())

    assert "secret-rumor" in listener.state.memory.rumors
    assert speaker.state.psyche.dialogue is None
    assert speaker.state.psyche.expression is not None
    assert speaker.state.psyche.expression.icon == Expressions.LOQUACITY.value