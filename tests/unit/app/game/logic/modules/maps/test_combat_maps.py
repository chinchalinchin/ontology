"""
# Ontology: tests.unit.app.game.logic.modules.maps.test_combat_maps.py
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Actions,
    Directions
)
from app.game.logic.modules.maps import CombatMap


@pytest.mark.combat
def test_combat_map_attackboxes_unarmed(mock_board):
    player = mock_board.player()
    player.state.inventory.equipment.weapon = None

    assert CombatMap.attackboxes(
        player.state, 
        mock_board.equipment
    ) == []


@pytest.mark.combat
def test_combat_map_attackboxes_missing_weapon_properties(mock_board):
    player = mock_board.player()
    player.state.inventory.equipment.weapon = "non-existent-weapon"

    assert CombatMap.attackboxes(
        player.state, 
        mock_board.equipment
    ) == []


@pytest.mark.combat
def test_combat_map_attackboxes_matching_frame(
    mock_board
):
    player = mock_board.player()
    equipment = mock_board.equipment

    player.state.inventory.equipment.weapon = "shortsword"
    player.state.animation.action = Actions.SLASH.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 3

    boxes = CombatMap.attackboxes(player.state, equipment)
    print(boxes)
    assert len(boxes) == 1
    assert boxes[0] == equipment.weapons['shortsword'].attackboxes['slash-right-3'][0]


@pytest.mark.combat
def test_combat_map_attackboxes_unmatched_frame(mock_board):
    player = mock_board.player()
    player.state.inventory.equipment.weapon = "shortsword"
    player.state.animation.action = Actions.SLASH.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 0

    assert CombatMap.attackboxes(player.state, mock_board.equipment) == []