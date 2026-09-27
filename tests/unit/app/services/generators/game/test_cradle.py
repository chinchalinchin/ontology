"""
# Ontology: tests.unit.services.generators.game.test_cradle
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    Reactions, 
    Inventories
)
from app.models.state import (
    Damage, 
    Lot
)

# Cython Libraries
from libs.core.models import (
    Velocity, 
    Position
)


@pytest.mark.services
def test_spawn_projectile(mock_cradle):
    pos = Position(x=50, y=50)
    vel = Velocity(vx=15, vy=0)
    
    asset = mock_cradle.spawn_projectile(
        "arrow-magic", 
        pos, 
        "layer_0",
        vel
    )
    
    assert asset.taxonomy.id == "arrow-magic"
    assert asset.taxonomy.category == AssetCategories.CURSORS
    assert asset.taxonomy.instance == AssetInstances.PROJECTILES
    
    assert asset.state.layer == "layer_0"
    assert asset.state.position == pos
    assert asset.state.velocity == vel
    assert asset.state.initial == pos


@pytest.mark.services
def test_spawn_strut(mock_cradle):
    pos = Position(x=100, y=100)
    
    asset = mock_cradle.spawn_strut(
        "frame-adobe", 
        pos, 
        "layer_0", 
        "player"
    )
    
    assert asset.taxonomy.id == "frame-adobe"
    assert asset.taxonomy.category == AssetCategories.CRAFTS
    assert asset.taxonomy.instance == AssetInstances.STRUTS
    
    assert asset.state.layer == "layer_0"
    assert asset.state.position == pos
    assert asset.state.owner == "player"


@pytest.mark.services
def test_spawn_collectable(mock_cradle):
    pos = Position(x=32, y=64)
    lot = Lot(
        inventory=Inventories.EQUIPMENT.value, 
        item="coin", 
        quantity=10
    )

    asset = mock_cradle.spawn_collectable(
        "gold-coin", 
        "layer_0", 
        pos, 
        lot
    )

    assert asset.taxonomy.id == "gold-coin"
    assert asset.taxonomy.category == AssetCategories.EFFECTS
    assert asset.taxonomy.instance == AssetInstances.COLLECTABLES
    assert asset.state.position == pos
    assert asset.state.layer == "layer_0"
    assert asset.state.lot.item == "coin"
    assert asset.state.lot.quantity == 10


@pytest.mark.services
def test_spawn_hazard(mock_cradle):
    pos = Position(x=120, y=80)
    damage = Damage(
        amount=25,
        duration=3, 
        reaction=Reactions.BOUNCE.value
    )

    asset = mock_cradle.spawn_hazard(
        "lava-pool", 
        "layer_0",
        pos, 
        damage
    )

    assert asset.taxonomy.id == "lava-pool"
    assert asset.taxonomy.category == AssetCategories.EFFECTS
    assert asset.taxonomy.instance == AssetInstances.HAZARDS
    assert asset.state.position == pos
    assert asset.state.layer == "layer_0"
    assert asset.state.damage.amount == 25
    assert asset.state.damage.reaction == Reactions.BOUNCE.value


@pytest.mark.services
def test_spawn_composition(mock_cradle):
    pos = Position(x=0, y=0)
        
    # Verify the composition generation offloads to the decomposer
    with patch.object(
        mock_cradle.decomposer, 
        "unpack", 
        wraps=mock_cradle.decomposer.unpack
    ) as mock_unpack:
        mock_cradle.spawn_composition(
            "brick-house", 
            pos, 
            "layer_0", 
            "player"
        )
        mock_unpack.assert_called_once()