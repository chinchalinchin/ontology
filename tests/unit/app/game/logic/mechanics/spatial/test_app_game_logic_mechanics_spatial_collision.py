"""
# Ontology: tests.unit.test_app_game_logic_mechanics_spatial_collision.py
"""
import pytest
import collections
from unittest.mock import MagicMock, patch

from app.game.logic.mechanics.spatial.collision import CollisionMechanics
from libs.core.models import Position, Dimensions, Hitbox, Boundary

def test_collision_mechanics_update(mock_board):
    """
    Verifies the two-phase collision pipeline: Environmental Constraints first, 
    Dynamic Entities second.
    """
    mechanic = CollisionMechanics()
    bus = collections.deque()
    payload = MagicMock()
    
    # Inject procedural perimeter into the mock board
    mock_boundary = Boundary(Position(0, 0), Dimensions(100, 1))
    mock_board.perimeters = {"0": [mock_boundary]}
    
    with patch.object(mechanic, 'constrain') as mock_constrain:
        with patch.object(mechanic, '_boundary') as mock_resolve_boundary:
            with patch.object(mechanic, 'collisions') as mock_collisions:
                with patch.object(mechanic, '_resolve') as mock_resolve:
                    
                    asset_a = mock_board.assets()[0]
                    asset_b = mock_board.assets()[2]
                    
                    # Mock collisions finding hits for both phases
                    mock_constrain.return_value = [(asset_a, mock_boundary)]
                    mock_collisions.return_value = [(asset_a, asset_b)]
                    
                    mechanic.update(mock_board, 0.016, bus, payload)
                    
                    # 1. Phase 1: Boundary constraints
                    mock_constrain.assert_called_once()
                    mock_resolve_boundary.assert_called_once_with(asset_a, mock_boundary)
                    
                    # 2. Phase 2: Dynamic entity constraints
                    mock_collisions.assert_called_once()
                    mock_resolve.assert_called_once_with(asset_a, asset_b)

def test_collision_mechanics_resolve():
    """
    Verifies Phase 2 standard narrow-phase geometry intersection.
    """
    mechanic = CollisionMechanics()
    
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
            mock_intersects.return_value = (asset_a.hitboxes[0], asset_b.hitboxes[0])
            
            mechanic._resolve(asset_a, asset_b)
            
            mock_intersects.assert_called_once()
            mock_collide.assert_called_once()

def test_collision_mechanics_resolve_boundary():
    """
    Verifies Phase 1 boundary-specific narrow-phase geometry intersection.
    """
    mechanic = CollisionMechanics()
    
    asset = MagicMock()
    asset.taxonomy.instance = "players"
    asset.state.position = Position(10, 10)
    asset.hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 32))]
    asset.state.velocity = None
    
    boundary = Boundary(Position(0, 0), Dimensions(100, 1))
    
    with patch('app.game.logic.mechanics.spatial.collision.geometry.bounded') as mock_intersects:
        with patch('app.game.logic.mechanics.spatial.collision.physics.constrain') as mock_constrain:
            mock_intersects.return_value = (asset.hitboxes[0],)
            
            mechanic._boundary(asset, boundary)
            
            mock_intersects.assert_called_once_with(
                10, 10, asset.hitboxes,
                0, 0, 100, 1
            )
            mock_constrain.assert_called_once()