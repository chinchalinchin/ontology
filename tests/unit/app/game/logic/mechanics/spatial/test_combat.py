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
import app.static.settings as settings
from app.static.semantics import (
    Actions,
    AssetInstances,
    Directions,
    Intentions,
    Mechanics,
)
from app.game.logic.modules.maps import CombatMap

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

@pytest.mark.workflow_combat
@pytest.mark.workflow_projectiles
def test_combat_mechanics_ranged_longbow_spawns_arrow(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()

    attacker.elevation = 1
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "longbow"
    attacker.state.animation.action = Actions.SHOOT.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 9
    attacker.state.animation.tick = 0
    attacker.state.character.strength = 10
    attacker.state.mutators.parameters.charge = settings.PROJECTILE_MAX_CHARGE_TICKS

    expected_speed = CombatMap.speed(attacker.state, mock_board.equipment)
    before = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))


    mechanic.update(mock_board, 0.016, mock_bus, payload)

    after = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))
    spawned = list(after - before)

    assert len(spawned) == 1
    arrow = spawned[0]
    assert arrow.id == "arrow"
    assert arrow.elevation == 1
    assert arrow.state.owner == attacker.name
    assert arrow.state.angle == 0
    assert arrow.state.speed == expected_speed
    assert arrow.state.velocity.vx == float(expected_speed)
    assert arrow.state.velocity.vy == 0.0
    # shoot-right-9 center = (2050, 2036), arrow 41x41 top-left = (2030, 2016)
    assert (arrow.state.position.x, arrow.state.position.y) == (2030, 2016)
    assert (arrow.state.initial.x, arrow.state.initial.y) == (2030, 2016)
    assert arrow.state.position is not arrow.state.initial
    assert attacker.state.mutators.parameters.charge == 0


@pytest.mark.workflow_combat
@pytest.mark.workflow_projectiles
def test_combat_mechanics_ranged_crossbow_spawns_bolt_without_melee(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """
    Verifies crossbow (Actions.THRUST) dispatches to _project via ProjectileIndex
    rather than executing melee damage on an adjacent target.
    """
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "crossbow"
    attacker.state.animation.action = Actions.THRUST.value
    attacker.state.animation.direction = Directions.DOWN.value
    attacker.state.animation.frame = 5
    attacker.state.animation.tick = 0
    attacker.state.character.strength = 20
    attacker.state.mutators.parameters.charge = 0

    # Place target overlapping thrust-down-5 release box (2028..2036, 2048..2056)
    hb = target.hitboxes[0]
    target.elevation = 0
    target.state.position = Position(2032 - hb.position.x, 2052 - hb.position.y)
    target.state.meters.health.current = 50
    target.state.mutators.triggers.dead = False

    expected_speed = CombatMap.speed(attacker.state, mock_board.equipment)
    before = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    after = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))
    spawned = list(after - before)

    assert len(spawned) == 1
    bolt = spawned[0]
    assert bolt.id == "bolt"
    assert bolt.state.owner == attacker.name
    assert bolt.state.angle == 90
    assert bolt.state.speed == expected_speed
    assert bolt.state.velocity.vx == 0.0
    assert bolt.state.velocity.vy == float(expected_speed)
    # thrust-down-5 center = (2032, 2052), bolt 32x32 top-left = (2016, 2036)
    assert (bolt.state.position.x, bolt.state.position.y) == (2016, 2036)
    # Target was not damaged by melee on the release tick
    assert target.state.meters.health.current == 50


@pytest.mark.workflow_combat
@pytest.mark.workflow_projectiles
def test_combat_mechanics_ranged_guards_non_entry_tick_and_non_release_frame(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "longbow"
    attacker.state.animation.action = Actions.SHOOT.value
    attacker.state.animation.direction = Directions.RIGHT.value

    before = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))

    # Non-entry tick on release frame
    attacker.state.animation.frame = 9
    attacker.state.animation.tick = 1
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert set(mock_board.instances(AssetInstances.PROJECTILES.value, "0")) == before

    # Entry tick on non-release frame
    attacker.state.animation.frame = 8
    attacker.state.animation.tick = 0
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert set(mock_board.instances(AssetInstances.PROJECTILES.value, "0")) == before


@pytest.mark.workflow_combat
@pytest.mark.workflow_projectiles
def test_combat_mechanics_ranged_charge_scales_launch_speed(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.COMBAT.value)
    payload = mock_payload()
    attacker = mock_board.player()

    attacker.elevation = 0
    attacker.state.position = Position(2000, 2000)
    attacker.state.intention = Intentions.ATTACK.value
    attacker.state.slots.equipment.weapon = "longbow"
    attacker.state.animation.action = Actions.SHOOT.value
    attacker.state.animation.direction = Directions.RIGHT.value
    attacker.state.animation.frame = 9
    attacker.state.animation.tick = 0
    attacker.state.character.strength = 10

    # Shot 1: Uncharged
    attacker.state.mutators.parameters.charge = 0
    before_1 = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    uncharged = next(iter(set(mock_board.instances(AssetInstances.PROJECTILES.value, "0")) - before_1))

    # Shot 2: Fully charged
    delay = CombatMap.delay(attacker.state, mock_board.equipment)
    full_charge = max(settings.PROJECTILE_MAX_CHARGE_TICKS, 9 * delay, 1)
    attacker.state.mutators.parameters.charge = full_charge
    before_2 = set(mock_board.instances(AssetInstances.PROJECTILES.value, "0"))
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    charged = next(iter(set(mock_board.instances(AssetInstances.PROJECTILES.value, "0")) - before_2))

    assert uncharged.state.speed == max(1, round(settings.PROJECTILE_BASE_SPEED_FACTOR * 10 * 1.0))
    assert charged.state.speed == max(1, round(settings.PROJECTILE_BASE_SPEED_FACTOR * 10 * 2.0))
    assert charged.state.speed > uncharged.state.speed