"""
# Ontology: tests.unit.test_app_game_logic_mechanics_spatial_collision.py
"""
import pytest
import collections
from unittest.mock import MagicMock, patch

from app.game.logic.mechanics.spatial.collision import CollisionMechanics
from libs.core.models import Position, Dimensions, Hitbox

def test_collision_mechanics_update(mock_board):
    mechanic = CollisionMechanics()
    bus = collections.deque()
    payload = MagicMock()
    
    with patch.object(mechanic, 'collisions') as mock_collisions:
        with patch.object(mechanic, '_resolve') as mock_resolve:
            # Setup mock collision pair using Board payload
            asset_a = mock_board.assets()[0]
            asset_b = mock_board.assets()[2]
            mock_collisions.return_value = [(asset_a, asset_b)]
            
            mechanic.update(mock_board, 0.016, bus, payload)
            
            # Verify struck mutation triggered (asset_a has mutators, tile doesn't)
            assert asset_a.state.mutators.triggers.struck is True
            assert asset_b.state.mutators.triggers.struck is True
            
            # Verify resolution hand-off
            mock_resolve.assert_called_once_with(asset_a, asset_b)

def test_collision_mechanics_resolve():
    mechanic = CollisionMechanics()
    
    # Mock Sprite vs Crate resolution
    asset_a = MagicMock()
    asset_a.taxonomy.instance = "players"
    asset_a.state.position = Position(10, 10)
    asset_a.dimensions = Dimensions(32, 32)
    asset_a.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 32))]
    
    asset_b = MagicMock()
    asset_b.taxonomy.instance = "crates"
    asset_b.state.position = Position(20, 20)
    asset_b.dimensions = Dimensions(32, 32)
    asset_b.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 32))]
    
    with patch('app.game.logic.mechanics.spatial.collision.geometry.intersects') as mock_intersects:
        with patch('app.game.logic.mechanics.spatial.collision.physics.collide') as mock_collide:
            
            # Simulate positive geometry narrow-phase overlap
            mock_intersects.return_value = (asset_a.hitboxes[0], asset_b.hitboxes[0])
            
            mechanic._resolve(asset_a, asset_b)
            
            mock_intersects.assert_called_once()
            mock_collide.assert_called_once()