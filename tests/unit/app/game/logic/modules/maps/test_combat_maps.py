"""
@domain.test
@test.unit
@app.module
@workflow.combat
@workflow.projectiles

# Ontology: tests.unit.app.game.logic.modules.maps.test_combat_maps

Unit tests for CombatMap.
"""
# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.game.logic.modules.maps import CombatMap
from app.static.semantics import (
    Actions,
    Directions,
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_module,
    pytest.mark.workflow_combat,
]

# -----------------------------------------------------


def test_combat_map_attackboxes_unarmed(mock_board):
    player = mock_board.player()
    player.state.slots.equipment.weapon = None

    assert CombatMap.attackboxes(
        player.state,
        mock_board.equipment,
    ) == []


def test_combat_map_attackboxes_missing_weapon_properties(mock_board):
    player = mock_board.player()
    player.state.slots.equipment.weapon = "non-existent-weapon"

    assert CombatMap.attackboxes(
        player.state,
        mock_board.equipment,
    ) == []


def test_combat_map_attackboxes_matching_frame(mock_board):
    player = mock_board.player()
    equipment = mock_board.equipment

    player.state.slots.equipment.weapon = "sword"
    player.state.animation.action = Actions.SLASH.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 3

    boxes = CombatMap.attackboxes(player.state, equipment)
    assert len(boxes) == 1
    assert boxes[0] == equipment.weapons["sword"].properties.hitboxes["slash-right-3"][0]


def test_combat_map_attackboxes_unmatched_frame(mock_board):
    player = mock_board.player()
    player.state.slots.equipment.weapon = "sword"
    player.state.animation.action = Actions.SLASH.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 0

    assert CombatMap.attackboxes(player.state, mock_board.equipment) == []


def test_combat_map_attackboxes_elevation_mismatch(mock_board):
    player = mock_board.player()
    player.state.elevation = 0
    player.state.slots.equipment.weapon = "sword"
    player.state.animation.action = Actions.SLASH.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 3

    assert CombatMap.attackboxes(player.state, mock_board.equipment, elevation=1) == []


@pytest.mark.workflow_projectiles
def test_combat_map_projectile_resolution(mock_board, mock_projectile_index):
    player = mock_board.player()

    player.state.slots.equipment.weapon = "longbow"
    assert CombatMap.projectile(player.state, mock_projectile_index) == "arrow"

    player.state.slots.equipment.weapon = "crossbow"
    assert CombatMap.projectile(player.state, mock_projectile_index) == "bolt"

    player.state.slots.equipment.weapon = "sword"
    assert CombatMap.projectile(player.state, mock_projectile_index) is None

    player.state.slots.equipment.weapon = None
    assert CombatMap.projectile(player.state, mock_projectile_index) is None

    player.state.slots.equipment.weapon = "longbow"
    assert CombatMap.projectile(player.state, None) is None

    player.state.slots = None
    assert CombatMap.projectile(player.state, mock_projectile_index) is None


@pytest.mark.workflow_projectiles
def test_combat_map_delay_resolution(mock_board):
    player = mock_board.player()
    equipment = mock_board.equipment

    player.state.slots.equipment.weapon = "longbow"
    player.state.animation.action = Actions.SHOOT.value
    expected_delay = max(
        1,
        equipment.weapons["longbow"].properties.actions[Actions.SHOOT.value].delay,
    )
    assert CombatMap.delay(player.state, equipment) == expected_delay

    # Missing action or unarmed falls back to 1
    player.state.animation.action = Actions.SLASH.value
    assert CombatMap.delay(player.state, equipment) == 1

    player.state.slots.equipment.weapon = None
    assert CombatMap.delay(player.state, equipment) == 1


@pytest.mark.workflow_projectiles
def test_combat_map_release_entry_tick_and_world_center(mock_board):
    player = mock_board.player()
    equipment = mock_board.equipment

    player.state.elevation = 0
    player.state.position = Position(2000, 2000)

    # Longbow release on shoot-right-9 (pos=(46, 32), dim=(8, 8) -> center=(2050, 2036))
    player.state.slots.equipment.weapon = "longbow"
    player.state.animation.action = Actions.SHOOT.value
    player.state.animation.direction = Directions.RIGHT.value
    player.state.animation.frame = 9
    player.state.animation.tick = 0

    release = CombatMap.release(player.state, equipment, elevation=0)
    assert release is not None
    spawn_pos, direction = release
    assert (spawn_pos.x, spawn_pos.y) == (2050, 2036)
    assert direction == Directions.RIGHT.value

    # Crossbow release on thrust-up-5 (pos=(28, 12), dim=(8, 8) -> center=(2032, 2016))
    player.state.slots.equipment.weapon = "crossbow"
    player.state.animation.action = Actions.THRUST.value
    player.state.animation.direction = Directions.UP.value
    player.state.animation.frame = 5
    player.state.animation.tick = 0

    release = CombatMap.release(player.state, equipment, elevation=0)
    assert release is not None
    spawn_pos, direction = release
    assert (spawn_pos.x, spawn_pos.y) == (2032, 2016)
    assert direction == Directions.UP.value
    
@pytest.mark.workflow_projectiles
def test_combat_map_release_guards_tick_frame_and_elevation(mock_board):
    player = mock_board.player()
    equipment = mock_board.equipment

    player.state.elevation = 0
    player.state.position = Position(2000, 2000)
    player.state.slots.equipment.weapon = "longbow"
    player.state.animation.action = Actions.SHOOT.value
    player.state.animation.direction = Directions.RIGHT.value

    # Non-entry tick suppresses release
    player.state.animation.frame = 9
    player.state.animation.tick = 1
    assert CombatMap.release(player.state, equipment, elevation=0) is None

    # Non-release frame suppresses release even on tick == 0
    player.state.animation.frame = 8
    player.state.animation.tick = 0
    assert CombatMap.release(player.state, equipment, elevation=0) is None

    # Mismatched elevation suppresses release
    player.state.animation.frame = 9
    player.state.animation.tick = 0
    assert CombatMap.release(player.state, equipment, elevation=1) is None


@pytest.mark.workflow_projectiles
def test_combat_map_speed_formula_and_saturation(mock_board):
    player = mock_board.player()
    equipment = mock_board.equipment

    player.state.slots.equipment.weapon = "longbow"
    player.state.animation.action = Actions.SHOOT.value
    player.state.animation.frame = 9
    player.state.character.strength = 10

    delay = CombatMap.delay(player.state, equipment)
    n_max = max(settings.PROJECTILE_MAX_CHARGE_TICKS, 9 * delay, 1)
    alpha = settings.PROJECTILE_BASE_SPEED_FACTOR

    # Uncharged (charge == 0) and negative charge clamp to tau == 0
    player.state.mutators.parameters.charge = 0
    assert CombatMap.speed(player.state, equipment) == max(1, round(alpha * 10 * 1.0))

    player.state.mutators.parameters.charge = -10
    assert CombatMap.speed(player.state, equipment) == max(1, round(alpha * 10 * 1.0))

    # Partial charge
    half_ticks = n_max // 2
    player.state.mutators.parameters.charge = half_ticks
    expected_half = max(1, round(alpha * 10 * (1.0 + (half_ticks / n_max))))
    assert CombatMap.speed(player.state, equipment) == expected_half

    # Full charge and over-hold saturation (tau capped at 1.0)
    player.state.mutators.parameters.charge = n_max
    full_speed = max(1, round(alpha * 10 * 2.0))
    assert CombatMap.speed(player.state, equipment) == full_speed

    player.state.mutators.parameters.charge = n_max * 5
    assert CombatMap.speed(player.state, equipment) == full_speed

    # Strength scaling
    player.state.character.strength = 20
    assert CombatMap.speed(player.state, equipment) == max(1, round(alpha * 20 * 2.0))