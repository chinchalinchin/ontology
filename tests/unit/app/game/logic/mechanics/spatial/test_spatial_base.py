"""
# Ontology: tests.unit.app.game.logic.mechanics.spatial.test_spatial_base
"""
# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import CollisionMechanics

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Hitbox
)


@pytest.mark.physics
def test_spatial_mechanic_center():
    mechanic = CollisionMechanics()
    pos = Position(10, 10)
    dim = Dimensions(32, 64)
    cx, cy = mechanic.center(pos, dim)

    assert cx == 26.0
    assert cy == 42.0


@pytest.mark.physics
def test_spatial_mechanic_collisions(mock_crate, mock_crate_alt, mock_strut):
    """
    Verifies Space broad-phase hashing and narrow-phase filtering with real fixtures.
    """
    mechanic = CollisionMechanics(cell_size=64, max_entities=100)

    mock_crate.state.position = Position(10, 10)
    mock_crate_alt.state.position = Position(20, 20)
    mock_strut.state.position = Position(200, 200)

    pairs = mechanic.collisions([mock_crate, mock_crate_alt, mock_strut])

    assert len(pairs) == 1
    assert (mock_crate, mock_crate_alt) in pairs or (mock_crate_alt, mock_crate) in pairs
    assert (mock_crate, mock_strut) not in pairs


@pytest.mark.physics
def test_spatial_mechanic_intersections(mock_crate, mock_chest):
    """
    Verifies virtual full-dimension hitbox generation for post-separation interaction checks.
    """
    mechanic = CollisionMechanics()

    mock_crate.state.position = Position(10, 10)
    mock_chest.state.position = Position(20, 20)

    pairs = mechanic.intersections([mock_crate, mock_chest])

    assert len(pairs) == 1
    assert (mock_crate, mock_chest) in pairs or (mock_chest, mock_crate) in pairs