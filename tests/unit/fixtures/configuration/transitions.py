"""
# Ontology: tests.unit.fixtures.configuration.transitions

Mock application configuration fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.config import (
    # ------- TRANSITION CONFIGURATION
    IntentionConfiguration,
    PlotConfiguration,
)

# --------------------------------------------------------------------------
# ------------------------------------------------------ MOCK CONFIGURATIONS
# --------------------------------------------------------------------------


@pytest.fixture 
def mock_plot_configuration():
    """
    """
    return {
        'town-locked': [
            PlotConfiguration(
                next='town-unlocked',
                conditions = ["'mayor_bribed' in plot.previous"]
            )
        ]   
    }


@pytest.fixture
def mock_intention_configuration():
    """
    Shared mock configurations covering various ISL edge cases.
    """
    return {
        "idle": [
            IntentionConfiguration(
                next="attack", 
                conditions=["sprite.meters.health.current < 50"]
            ),
            IntentionConfiguration(
                next="wander", 
                conditions=["sprite.meters.health.current >= 50"]
            )
        ],
        "attack": [
            IntentionConfiguration(
                next="idle", 
                conditions=["sprites.get('enemy') and sprites.get('enemy').mutators.triggers.dead"]
            )
        ],
        "find": [
            IntentionConfiguration(
                next="interact",
                conditions=[
                    "sprite.goal",
                    "sprites.get(sprite.goal.name)",
                    "functions.is_near(sprite.position, sprites.get(sprite.goal.name).position, 10)"
                ]
            )
        ],
        "bad_syntax": [
            IntentionConfiguration(
                next="idle", 
                conditions=["sprite.meters.health.current =="]
            ) # syntax error
        ]
    }
