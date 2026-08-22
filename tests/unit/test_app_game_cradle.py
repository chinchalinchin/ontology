"""
# Ontology: tests.unit.test_app_game_cradle
"""
import pytest
from unittest.mock import MagicMock
from app.game.cradle import Cradle
from app.config.enums import AssetCategories, AssetInstances
from libs.core.models import Velocity, Position

@pytest.fixture
def cradle(mock_spawnables, mock_configurations):
    decomposer = MagicMock()
    return Cradle(mock_spawnables, mock_configurations.recipes, decomposer)

def test_spawn_projectile(cradle):
    pos = Position(x=50, y=50)
    vel = Velocity(vx=15, vy=0)
    
    asset = cradle.spawn_projectile("arrow-magic", pos, "layer_0", vel)
    
    assert asset.taxonomy.id == "arrow-magic"
    assert asset.taxonomy.category == AssetCategories.CURSORS
    assert asset.taxonomy.instance == AssetInstances.PROJECTILES
    
    assert asset.state.layer == "layer_0"
    assert asset.state.position == pos
    assert asset.state.velocity == vel
    assert asset.state.initial == pos

def test_spawn_strut(cradle):
    pos = Position(x=100, y=100)
    
    asset = cradle.spawn_strut("frame-adobe", pos, "layer_0", "player")
    
    assert asset.taxonomy.id == "frame-adobe"
    assert asset.taxonomy.category == AssetCategories.CRAFTS
    assert asset.taxonomy.instance == AssetInstances.STRUTS
    
    assert asset.state.layer == "layer_0"
    assert asset.state.position == pos
    assert asset.state.owner == "player"

def test_spawn_composition(cradle):
    pos = Position(x=0, y=0)
    
    cradle.spawn_composition("brick-house", pos, "layer_0", "player")
    
    # Verify the composition generation offloads to the decomposer
    cradle.decomposer.unpack.assert_called_once()