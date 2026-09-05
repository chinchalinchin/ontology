import pytest
from unittest.mock import MagicMock
from app.game.logic.mechanics.motion import frictive

def test_frictive_update_partial_decay(mock_crate, mock_board):
    # Set initial velocity moving right
    mock_crate.state.velocity.vx = 10.0
    mock_crate.state.velocity.vy = 0.0
    
    # Mock the tile lookup and friction assignment
    tile = MagicMock()
    tile.properties.friction = 5.0
    mock_board.tile = MagicMock(return_value=tile)
    
    # dv = friction * delta = 5.0 * 1.0 = 5.0
    frictive.update([mock_crate], mock_board, 1.0)
    
    assert mock_crate.state.velocity.vx == 5.0
    assert mock_crate.state.velocity.vy == 0.0

def test_frictive_update_full_stop(mock_crate, mock_board):
    # Assign a 3-4-5 triangle vector magnitude
    mock_crate.state.velocity.vx = 4.0
    mock_crate.state.velocity.vy = 3.0
    
    tile = MagicMock()
    tile.properties.friction = 10.0  # dv = 10.0 (greater than magnitude of 5.0)
    mock_board.tile = MagicMock(return_value=tile)
    
    frictive.update([mock_crate], mock_board, 1.0)
    
    # Assert crate has fully come to a halt
    assert mock_crate.state.velocity.vx == 0.0
    assert mock_crate.state.velocity.vy == 0.0

def test_frictive_no_velocity(mock_crate, mock_board):
    mock_crate.state.velocity = None
    mock_board.tile = MagicMock()
    
    # Execution should bypass the loop without throwing exceptions
    frictive.update([mock_crate], mock_board, 1.0)
    assert not mock_board.tile.called