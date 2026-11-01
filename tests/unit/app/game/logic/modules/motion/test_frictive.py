"""
@domain.test
@test.unit
@physics.motion

# Ontology: Tests - tests.unit.game.logic.modules.motion.test_frictive

Unit tests for the frictive motion module.
"""
# Standard Libaries
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
from app.game.logic.modules.motion import frictive
from app.static.semantics import (
    AssetCategories,
    AssetInstances
)

@pytest.mark.physics_motion
def test_frictive_update_partial_decay(mock_board):
    mock_crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    # Set initial velocity moving right
    mock_crate.state.velocity.vx = 10.0
    mock_crate.state.velocity.vy = 0.0

    mock_tile = mock_board.instances(AssetInstances.ENVIRON.value)[0]
    mock_tile.properties.friction = 5.0
    
    # dv = friction * delta = 5.0 * 1.0 = 5.0
    frictive.update([mock_crate], mock_board, 1.0)
    
    assert mock_crate.state.velocity.vx == 5.0
    assert mock_crate.state.velocity.vy == 0.0


@pytest.mark.physics_motion
def test_frictive_update_full_stop(mock_board):
    mock_crate = mock_board.instances(AssetInstances.CRATES.value)[0]

    # Assign a 3-4-5 triangle vector magnitude
    mock_crate.state.velocity.vx = 4.0
    mock_crate.state.velocity.vy = 3.0
    
    mock_tile = mock_board.instances(AssetInstances.ENVIRON.value)[0]
    mock_tile.properties.friction = 10.0  # dv = 10.0 (greater than magnitude of 5.0)
    
    frictive.update([mock_crate], mock_board, 1.0)
    
    # Assert crate has fully come to a halt
    assert mock_crate.state.velocity.vx == 0.0
    assert mock_crate.state.velocity.vy == 0.0