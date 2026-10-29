"""
@domain.test
@test.unit
@app.services
@workflow.injection

# Ontology: Tests - tests.unit.services.generators.game.test_cradle

Unit tests for the Cradle class.
"""
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
    pytest.mark.app_services,
    pytest.mark.workflow_injection,
]

# ------------------------------------------------------------------


@pytest.mark.category_cursors
def test_spawn_projectile(mock_cradle):
    pos = Position(x=50, y=50)
    vel = Velocity(vx=15, vy=0)
    proj_id = next(iter(mock_cradle.spawnables.projectiles.keys()))

    asset = mock_cradle.spawn_projectile(
        proj_id,
        pos,
        "0",
        vel,
    )

    assert asset.taxonomy.id == proj_id
    assert asset.taxonomy.category == AssetCategories.CURSORS.value
    assert asset.taxonomy.instance == AssetInstances.PROJECTILES.value
    assert asset.state.layer == "0"
    assert asset.state.position == pos
    assert asset.state.velocity == vel
    assert asset.state.initial == pos


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