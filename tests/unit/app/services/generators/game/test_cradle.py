"""
@domain.test
@test.unit
@app.service
@workflow.injection
@workflow.projectiles

# Ontology: Tests - tests.unit.services.generators.game.test_cradle

Unit tests for the Cradle class.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Buildings,
    Ceramics,
    Geologics,
    Inventories,
    Orientations,
    Reactions,
    Directions
)
from app.models.state import (
    Damage,
    Lot,
)

# Cython Libraries
from libs.core.models import (
    Multiple,
    Position,
    Velocity,
)

# ------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
    pytest.mark.workflow_injection,
]

# ------------------------------------------------------------------


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
@pytest.mark.parametrize(
    "direction, expected_angle, expected_vx, expected_vy",
    [
        (Directions.RIGHT.value, 0, 180.0, 0.0),
        (Directions.DOWN.value, 90, 0.0, 180.0),
        (Directions.LEFT.value, 180, -180.0, 0.0),
        (Directions.UP.value, 270, 0.0, -180.0),
    ],
)
def test_spawn_projectile_cardinal_directions(
    mock_cradle,
    direction: str,
    expected_angle: int,
    expected_vx: float,
    expected_vy: float,
):
    """Verifies centering, distinct initial/position objects, and exact cardinal velocities."""
    release_pos = Position(x=100, y=120)

    asset = mock_cradle.spawn_projectile(
        id="arrow",
        position=release_pos,
        layer="0",
        direction=direction,
        speed=180,
        elevation=2,
        owner="player",
    )

    assert asset.taxonomy.id == "arrow"
    assert asset.taxonomy.category == AssetCategories.CURSORS.value
    assert asset.taxonomy.instance == AssetInstances.PROJECTILES.value
    assert asset.state.layer == "0"
    assert asset.state.elevation == 2
    assert asset.state.owner == "player"
    assert asset.state.angle == expected_angle
    assert asset.state.speed == 180
    # arrow dimensions: 41x41 -> centered top-left = (100 - 20, 120 - 20)
    assert (asset.state.position.x, asset.state.position.y) == (80, 100)
    assert (asset.state.initial.x, asset.state.initial.y) == (80, 100)
    assert asset.state.position is not asset.state.initial
    assert (asset.state.velocity.vx, asset.state.velocity.vy) == (expected_vx, expected_vy)


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
def test_spawn_projectile_target_angle_quantization(mock_cradle):
    """Verifies target displacement quantization onto properties.rotation and zero-vector fallback."""
    origin = Position(x=200, y=200)

    # 45-degree rotation step on cannonball (16x16) toward down-right target
    ball = mock_cradle.spawn_projectile(
        id="cannonball",
        position=origin,
        layer="0",
        target=Position(x=300, y=300),
        speed=200,
    )
    assert (ball.state.position.x, ball.state.position.y) == (192, 192)
    assert ball.state.angle == 45
    assert ball.state.velocity.vx == pytest.approx(200 * math.cos(math.radians(45)))
    assert ball.state.velocity.vy == pytest.approx(200 * math.sin(math.radians(45)))

    # 90-degree rotation step on arrow quantizes ~11.3 deg down-right to 0 deg
    arrow = mock_cradle.spawn_projectile(
        id="arrow",
        position=origin,
        layer="0",
        target=Position(x=300, y=220),
        speed=150,
    )
    assert arrow.state.angle == 0
    assert (arrow.state.velocity.vx, arrow.state.velocity.vy) == (150.0, 0.0)

    # Zero displacement target falls back to explicit direction
    fallback = mock_cradle.spawn_projectile(
        id="arrow",
        position=origin,
        layer="0",
        direction=Directions.LEFT.value,
        target=Position(x=200, y=200),
        speed=150,
    )
    assert fallback.state.angle == 180
    assert (fallback.state.velocity.vx, fallback.state.velocity.vy) == (-150.0, 0.0)


@pytest.mark.category_cursors
@pytest.mark.workflow_projectiles
def test_spawn_projectile_default_angle_and_unknown_id(mock_cradle):
    """Verifies omitted direction/target defaults to 0 degrees and unknown IDs raise ValueError."""
    asset = mock_cradle.spawn_projectile(
        id="bolt",
        position=Position(x=64, y=64),
        layer="0",
    )
    assert (asset.state.position.x, asset.state.position.y) == (48, 48)
    assert asset.state.angle == 0
    assert asset.state.speed == 200
    assert (asset.state.velocity.vx, asset.state.velocity.vy) == (200.0, 0.0)

    with pytest.raises(ValueError, match="Unknown projectile asset ID"):
        mock_cradle.spawn_projectile(
            id="non-existent-projectile",
            position=Position(x=64, y=64),
            layer="0",
        )
        

@pytest.mark.category_crafts
def test_spawn_bridge(mock_cradle):
    pos = Position(x=30, y=290)

    assets = mock_cradle.spawn_bridge(
        "arch",
        "0",
        pos,
        Geologics.GRANITE.value,
        Orientations.HORIZONTAL.value,
        Multiple(nx=2, ny=0),
    )

    assert len(assets) == 2
    for asset in assets:
        assert asset.taxonomy.id == "arch"
        assert asset.taxonomy.category == AssetCategories.CRAFTS.value
        assert asset.taxonomy.instance == AssetInstances.BRIDGES.value
        assert asset.state.layer == "0"
        assert asset.state.material == Geologics.GRANITE.value
        assert asset.state.blueprint == Orientations.HORIZONTAL.value


@pytest.mark.category_effects
def test_spawn_collectable(mock_cradle):
    pos = Position(x=32, y=64)
    lot = Lot(
        inventory=Inventories.EQUIPMENT.value,
        item="coin",
        quantity=10,
    )

    asset = mock_cradle.spawn_collectable(
        "coin",
        "0",
        pos,
        lot,
    )

    assert asset.taxonomy.id == "coin"
    assert asset.taxonomy.category == AssetCategories.EFFECTS.value
    assert asset.taxonomy.instance == AssetInstances.COLLECTABLES.value
    assert asset.state.position == pos
    assert asset.state.layer == "0"
    assert asset.state.lot.item == "coin"
    assert asset.state.lot.quantity == 10


@pytest.mark.category_effects
def test_spawn_hazard(mock_cradle):
    pos = Position(x=120, y=80)
    damage = Damage(
        amount=25,
        duration=3,
        reaction=Reactions.BOUNCE.value,
    )

    asset = mock_cradle.spawn_hazard(
        "lava",
        "0",
        pos,
        damage,
    )

    assert asset.taxonomy.id == "lava"
    assert asset.taxonomy.category == AssetCategories.EFFECTS.value
    assert asset.taxonomy.instance == AssetInstances.HAZARDS.value
    assert asset.state.position == pos
    assert asset.state.layer == "0"
    assert asset.state.damage.amount == 25
    assert asset.state.damage.reaction == Reactions.BOUNCE.value


@pytest.mark.workflow_compositions
def test_spawn_composition(mock_cradle):
    pos = Position(x=250, y=100)

    assets = mock_cradle.spawn_composition(
        "brick-house",
        pos,
        Ceramics.CLAY.value,
        Buildings.WALLS.value,
        "0",
        "player",
    )

    assert len(assets) > 0
    assert any(a.state.layer == "0" for a in assets)