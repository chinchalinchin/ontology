"""
@domain.test
@test.unit
@app.mechanic
@physics.space
@workflow.projectiles

# Ontology: Tests - tests.unit.app.game.logic.mechanics.spatial.test_projectile

Unit tests for ProjectileMechanics.
"""
# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Directions,
    Intentions,
    Mechanics,
)

# Cython Libraries
from libs.core.models import (
    Boundary,
    Dimensions,
    Position,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_mechanic,
    pytest.mark.physics_space,
    pytest.mark.workflow_projectiles,
]

# -----------------------------------------------------


def test_projectile_mechanics_range_expiration(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()

    proj = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=Position(1300, 2000),
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=0,
    )
    mock_board.add([proj])

    # Within max range -> survives
    proj.state.position.x = proj.state.initial.x + settings.PROJECTILE_MAX_RANGE - 1
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert proj in mock_board.instances(AssetInstances.PROJECTILES.value, "0")

    # At max range -> expired and removed
    proj.state.position.x = proj.state.initial.x + settings.PROJECTILE_MAX_RANGE
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert proj not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")


def test_projectile_mechanics_layer_bounds_expiration(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()

    tiles = mock_board.categories(AssetCategories.TILES.value, "0")
    layer_w = max(
        int(t.state.position.x) + (t.state.multiple.nx * t.properties.dimensions.w)
        for t in tiles
    )

    # Initial matches position so out_of_range is False; strictly tests out_of_bounds
    p_left = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=Position(-100, 2000),
        layer="0",
        direction=Directions.LEFT.value,
    )
    p_right = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=Position(layer_w + 100, 2000),
        layer="0",
        direction=Directions.RIGHT.value,
    )
    mock_board.add([p_left, p_right])

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    active = mock_board.instances(AssetInstances.PROJECTILES.value, "0")
    assert p_left not in active
    assert p_right not in active


def test_projectile_mechanics_ground_perimeter_expiration_and_elevated_bypass(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()

    # Inject an isolated ground-tier perimeter boundary at (2100, 2000)
    mock_board.perimeters["0"][0].append(
        Boundary(Position(2100, 2000), Dimensions(4, 100))
    )

    p_ground = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=Position(2102, 2050),
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=0,
    )
    p_elevated = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=Position(2102, 2050),
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=1,
    )
    mock_board.add([p_ground, p_elevated])

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    active = mock_board.instances(AssetInstances.PROJECTILES.value, "0")
    assert p_ground not in active
    assert p_elevated in active


@pytest.mark.workflow_combat
def test_projectile_mechanics_hits_sprite_applies_damage_and_removes(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    target.elevation = 0
    target.state.position = Position(2000, 2000)
    target.state.character.defense = 5
    target.state.meters.health.current = 50
    target.state.mutators.triggers.dead = False

    hb = target.hitboxes[0]
    hit_center = Position(
        target.state.position.x + hb.position.x + (hb.dimensions.w // 2),
        target.state.position.y + hb.position.y + (hb.dimensions.l // 2),
    )

    # speed / alpha == 20 -> damage = max(1, 20 - 5) = 15
    proj = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=hit_center,
        layer="0",
        direction=Directions.RIGHT.value,
        speed=20 * settings.PROJECTILE_BASE_SPEED_FACTOR,
        elevation=0,
        owner="player",
    )
    mock_board.add([proj])

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert target.state.meters.health.current == 35
    assert target.state.mutators.triggers.dead is False
    assert proj not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")


@pytest.mark.workflow_combat
def test_projectile_mechanics_hits_player_minimum_damage_and_lethal_blow(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    player = mock_board.player()

    player.elevation = 0
    player.state.position = Position(2000, 2000)
    player.state.mutators.triggers.dead = False

    hb = player.hitboxes[0]
    hit_center = Position(
        player.state.position.x + hb.position.x + (hb.dimensions.w // 2),
        player.state.position.y + hb.position.y + (hb.dimensions.l // 2),
    )

    # Case 1: Defense exceeds raw power -> minimum 1 damage
    player.state.character.defense = 50
    player.state.meters.health.current = 10
    p_weak = mock_board.cradle.spawn_projectile(
        id="bolt",
        position=hit_center,
        layer="0",
        direction=Directions.LEFT.value,
        speed=5 * settings.PROJECTILE_BASE_SPEED_FACTOR,
        elevation=0,
        owner="test-sprite-0",
    )
    mock_board.add([p_weak])
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.meters.health.current == 9
    assert player.state.mutators.triggers.dead is False
    assert p_weak not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")

    # Case 2: Lethal blow clamps health to 0 and triggers dead mutator
    player.state.character.defense = 0
    player.state.meters.health.current = 5
    p_lethal = mock_board.cradle.spawn_projectile(
        id="bolt",
        position=hit_center,
        layer="0",
        direction=Directions.LEFT.value,
        speed=20 * settings.PROJECTILE_BASE_SPEED_FACTOR,
        elevation=0,
        owner="test-sprite-0",
    )
    mock_board.add([p_lethal])
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert player.state.meters.health.current == 0
    assert player.state.mutators.triggers.dead is True
    assert p_lethal not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")


@pytest.mark.workflow_combat
def test_projectile_mechanics_excludes_owner_and_dead_targets(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    player = mock_board.player()
    corpse = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    player.elevation = 0
    player.state.position = Position(2000, 2000)
    player.state.meters.health.current = 50
    player.state.mutators.triggers.dead = False

    p_hb = player.hitboxes[0]
    p_center = Position(
        player.state.position.x + p_hb.position.x + (p_hb.dimensions.w // 2),
        player.state.position.y + p_hb.position.y + (p_hb.dimensions.l // 2),
    )

    corpse.elevation = 0
    corpse.state.position = Position(2300, 2000)
    corpse.state.meters.health.current = 0
    corpse.state.mutators.triggers.dead = True

    c_hb = corpse.hitboxes[0]
    c_center = Position(
        corpse.state.position.x + c_hb.position.x + (c_hb.dimensions.w // 2),
        corpse.state.position.y + c_hb.position.y + (c_hb.dimensions.l // 2),
    )

    p_self = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=p_center,
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=0,
        owner=player.name,
    )
    p_over_corpse = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=c_center,
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=0,
        owner=player.name,
    )
    mock_board.add([p_self, p_over_corpse])

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    active = mock_board.instances(AssetInstances.PROJECTILES.value, "0")
    assert player.state.meters.health.current == 50
    assert p_self in active
    assert p_over_corpse in active


@pytest.mark.workflow_combat
def test_projectile_mechanics_elevation_isolation(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    target = mock_board.instances(AssetInstances.SPRITES.value, "0")[0]

    target.elevation = 1
    target.state.position = Position(2000, 2000)
    target.state.character.defense = 0
    target.state.meters.health.current = 50
    target.state.mutators.triggers.dead = False

    hb = target.hitboxes[0]
    hit_center = Position(
        target.state.position.x + hb.position.x + (hb.dimensions.w // 2),
        target.state.position.y + hb.position.y + (hb.dimensions.l // 2),
    )

    # Elevation 0 projectile passes underneath elevation 1 target
    p_low = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=hit_center,
        layer="0",
        direction=Directions.RIGHT.value,
        speed=10 * settings.PROJECTILE_BASE_SPEED_FACTOR,
        elevation=0,
        owner="player",
    )
    mock_board.add([p_low])
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert target.state.meters.health.current == 50
    assert p_low in mock_board.instances(AssetInstances.PROJECTILES.value, "0")

    # Elevation 1 projectile hits elevation 1 target
    p_high = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=hit_center,
        layer="0",
        direction=Directions.RIGHT.value,
        speed=10 * settings.PROJECTILE_BASE_SPEED_FACTOR,
        elevation=1,
        owner="player",
    )
    mock_board.add([p_high])
    mechanic.update(mock_board, 0.016, mock_bus, payload)

    assert target.state.meters.health.current == 40
    assert p_high not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")


@pytest.mark.workflow_combat
def test_projectile_mechanics_activates_attack_reactable_only(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    dummy = mock_board.instances(AssetInstances.REACTABLES.value, "0")[0]

    dummy.elevation = 0
    dummy.state.position = Position(2000, 2000)
    dummy.state.active = False

    hb = dummy.hitboxes[0]
    hit_center = Position(
        dummy.state.position.x + hb.position.x + (hb.dimensions.w // 2),
        dummy.state.position.y + hb.position.y + (hb.dimensions.l // 2),
    )

    proj = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=hit_center,
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=0,
        owner="player",
    )
    mock_board.add([proj])

    # Non-attack reactable is ignored
    dummy.state.intention = Intentions.INTERACT.value
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert dummy.state.active is False
    assert proj in mock_board.instances(AssetInstances.PROJECTILES.value, "0")

    # Attack reactable activates and consumes projectile
    dummy.state.intention = Intentions.ATTACK.value
    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert dummy.state.active is True
    assert proj not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")


def test_projectile_mechanics_obstacle_impact_removes_projectile(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    obstacle = next(
        o
        for o in mock_board.obstacles("0", 0)
        if o.instance not in (
            AssetInstances.SPRITES.value,
            AssetInstances.PLAYERS.value,
            AssetInstances.REACTABLES.value,
        )
        and o.hitbox.get(o.properties, o.state, 0)
    )

    obstacle.state.position = Position(2000, 2000)
    hb = obstacle.hitbox.get(obstacle.properties, obstacle.state, 0)[0]
    hit_center = Position(
        obstacle.state.position.x + hb.position.x + (hb.dimensions.w // 2),
        obstacle.state.position.y + hb.position.y + (hb.dimensions.l // 2),
    )

    proj = mock_board.cradle.spawn_projectile(
        id="cannonball",
        position=hit_center,
        layer="0",
        direction=Directions.RIGHT.value,
        elevation=0,
        owner="player",
    )
    mock_board.add([proj])

    mechanic.update(mock_board, 0.016, mock_bus, payload)
    assert proj not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")

@pytest.mark.workflow_combat
def test_projectile_mechanics_single_impact_per_projectile(
    mock_mechanic,
    mock_board,
    mock_bus,
    mock_payload,
):
    """Verifies a single projectile impacts at most one target when overlapping multiple sprites."""
    mechanic = mock_mechanic(Mechanics.PROJECTILE.value)
    payload = mock_payload()
    sprite_a, sprite_b = mock_board.instances(AssetInstances.SPRITES.value, "0")[:2]

    for sprite in (sprite_a, sprite_b):
        sprite.elevation = 0
        sprite.state.position = Position(2000, 2000)
        sprite.state.character.defense = 0
        sprite.state.meters.health.current = 50
        sprite.state.mutators.triggers.dead = False

    hb = sprite_a.hitboxes[0]
    hit_center = Position(
        sprite_a.state.position.x + hb.position.x + (hb.dimensions.w // 2),
        sprite_a.state.position.y + hb.position.y + (hb.dimensions.l // 2),
    )

    proj = mock_board.cradle.spawn_projectile(
        id="arrow",
        position=hit_center,
        layer="0",
        direction=Directions.RIGHT.value,
        speed=10 * settings.PROJECTILE_BASE_SPEED_FACTOR,
        elevation=0,
        owner="player",
    )
    mock_board.add([proj])

    mechanic.update(mock_board, 0.016, mock_bus, payload)

    damaged_count = sum(
        1
        for sprite in (sprite_a, sprite_b)
        if sprite.state.meters.health.current < 50
    )
    assert damaged_count == 1
    assert proj not in mock_board.instances(AssetInstances.PROJECTILES.value, "0")