"""
@domain.test
@test.unit
@app.mechanic
@physics.space
@category.sheets
@workflow.combat

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_combat

Unit tests for CombatMechanics.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Actions,
    AssetInstances,
    Directions,
    Intentions,
    Mechanics,
)

# Cython Libraries
from libs.core.models import (
    Position,
    Velocity,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.physics_space,
    pytest.mark.workflow_combat,
]

# -----------------------------------------------------


@pytest.mark.workflow_combat
def test_combat_mechanics_melee_resolution(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "sword"
    attacker.state.animation.action = Actions.SLASH.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 3
    attacker.state.character.strength = 20

    target.elevation = 0
    target.state.position = Position(2025, 2015)
    target.state.character.defense = 5
    target.state.meters.health.current = 50
    target.state.mutators.triggers.dead = False

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    # Strength 20 - Defense 5 = 15 damage (50 -> 35)
    assert target.state.meters.health.current == 35
    assert target.state.mutators.triggers.dead is False


@pytest.mark.workflow_combat
def test_combat_mechanics_lethal_blow(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "sword"
    attacker.state.animation.action = Actions.SLASH.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 3
    attacker.state.character.strength = 100

    target.elevation = 0
    target.state.position = Position(2025, 2015)
    target.state.character.defense = 0
    target.state.meters.health.current = 10
    target.state.mutators.triggers.dead = False

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert target.state.meters.health.current == 0
    assert target.state.mutators.triggers.dead is True


@pytest.mark.workflow_combat
def test_combat_mechanics_reactable_trigger(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    dummy = mock_board.instances(AssetInstances.REACTABLES.value, "0")[0]

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "sword"
    attacker.state.animation.action = Actions.SLASH.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 3

    hb = dummy.hitboxes[0]
    dummy.elevation = 0
    dummy.state.position = Position(2046 - hb.position.x, 2044 - hb.position.y)
    dummy.state.intention = Intentions.ATTACK.value
    dummy.state.active = False

    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert dummy.state.active is True


@pytest.mark.workflow_combat
def test_combat_mechanics_inactive_attackbox_filtered(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    # Frame 0 has no active attackboxes configured
    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "sword"
    attacker.state.animation.action = Actions.SLASH.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 0

    target.elevation = 0
    target.state.position = Position(2025, 2015)
    target.state.meters.health.current = 50

    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert target.state.meters.health.current == 50


@pytest.mark.workflow_combat
def test_combat_mechanics_unarmed_bypasses_melee(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = None
    attacker.state.animation.action = Actions.CAST.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 0

    target.elevation = 0
    target.state.position = Position(2025, 2015)
    target.state.meters.health.current = 50

    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert target.state.meters.health.current == 50


@pytest.mark.workflow_combat
def test_combat_mechanics_elevation_isolation(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "sword"
    attacker.state.animation.action = Actions.SLASH.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 3
    attacker.state.character.strength = 20

    target.elevation = 1
    target.state.position = Position(2025, 2015)
    target.state.character.defense = 5
    target.state.meters.health.current = 50
    target.state.mutators.triggers.dead = False

    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert target.state.meters.health.current == 50

    target.elevation = 0
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert target.state.meters.health.current == 35