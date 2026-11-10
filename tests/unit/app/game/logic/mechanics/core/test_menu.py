"""
@domain.test
@test.unit
@app.core
@app.mechanic
@app.menu

# Ontology: Tests - tests.unit.app.game.logic.mechanics.core.test_animation

Unit tests for the AnimationMechanics implementation.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Mechanics,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_core,
    pytest.mark.app_mechanic
]

# -----------------------------------------------------

# TODO: