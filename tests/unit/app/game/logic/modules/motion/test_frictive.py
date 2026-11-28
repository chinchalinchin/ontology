"""
@domain.test
@test.unit
@app.module
@physics.motion

# Ontology: Tests - tests.unit.game.logic.modules.motion.test_frictive

Unit tests for the frictive motion module.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.modules.motion import frictive
from app.static.semantics import AssetInstances

from libs.core.models import (
    Position, 
    Velocity
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

@pytest.mark.physics_motion
@pytest.mark.workflow_gravity
def test_frictive_update_skips_falling_asset(mock_board):
    """Verifies airborne frictive assets bypass tile friction decay."""
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.mutators.triggers.falling = True
    crate.state.velocity = Velocity(20.0, -5.0)

    frictive.update([crate], mock_board, 1.0)

    assert crate.state.velocity.vx == 20.0
    assert crate.state.velocity.vy == -5.0


@pytest.mark.physics_motion
def test_frictive_update_skips_none_velocity(mock_board):
    """Verifies assets with velocity=None exit cleanly without raising."""
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.velocity = None

    frictive.update([crate], mock_board, 1.0)

    assert crate.state.velocity is None


@pytest.mark.physics_motion
@pytest.mark.workflow_fluids
def test_frictive_update_suspended_in_fluid(mock_board):
    """Verifies tile friction decay is suspended while a crate center lies in active fluid."""
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    fluid = mock_board.instances(AssetInstances.FLUIDS.value)[0]
    hb = fluid.hitboxes[0]

    target_x = fluid.state.position.x + hb.position.x + (hb.dimensions.w // 2)
    target_y = fluid.state.position.y + hb.position.y + (hb.dimensions.l // 2)

    crate.state.layer = fluid.state.layer
    crate.state.mutators.triggers.falling = False
    crate.state.position = Position(
        target_x - (crate.dimensions.w // 2),
        target_y - (crate.dimensions.l // 2),
    )
    crate.state.velocity = Velocity(15.0, 0.0)

    frictive.update([crate], mock_board, 1.0)

    assert crate.state.velocity.vx == 15.0
    assert crate.state.velocity.vy == 0.0


@pytest.mark.physics_motion
def test_frictive_update_skips_when_no_tile_underneath(mock_board):
    """Verifies assets positioned outside environ tile coverage retain velocity safely."""
    crate = mock_board.instances(AssetInstances.CRATES.value)[0]
    crate.state.mutators.triggers.falling = False
    crate.state.position = Position(-10000, -10000)
    crate.state.velocity = Velocity(12.0, 0.0)

    frictive.update([crate], mock_board, 1.0)

    assert crate.state.velocity.vx == 12.0
    assert crate.state.velocity.vy == 0.0