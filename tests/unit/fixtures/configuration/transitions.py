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
    StageConfiguration
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


@pytest.fixture
def mock_stage_configuration():
    """Declarative stage transitions across annual and perennial lifespans."""
    return {
        "annual": {
            "sprout": [
                StageConfiguration(
                    next="growth",
                    conditions=[
                        "calendar.season in [constants.Seasons.SPRING.value, constants.Seasons.SUMMER.value]",
                        "resource.retention >= 20.0"
                    ]
                ),
                StageConfiguration(
                    next="stump",
                    conditions=["calendar.season == constants.Seasons.WINTER.value"]
                )
            ],
            "growth": [
                StageConfiguration(
                    next="stalk",
                    conditions=[
                        "calendar.season in [constants.Seasons.SPRING.value, constants.Seasons.SUMMER.value]",
                        "resource.retention >= 25.0"
                    ]
                ),
                StageConfiguration(
                    next="stump",
                    conditions=["calendar.season == constants.Seasons.WINTER.value"]
                )
            ],
            "stalk": [
                StageConfiguration(
                    next="bloom",
                    conditions=[
                        "calendar.season == constants.Seasons.AUTUMN.value",
                        "resource.retention >= 30.0"
                    ]
                ),
                StageConfiguration(
                    next="stump",
                    conditions=["calendar.season == constants.Seasons.WINTER.value"]
                )
            ],
            "bloom": [
                StageConfiguration(
                    next="stump",
                    conditions=[
                        "calendar.season == constants.Seasons.AUTUMN.value",
                        "resource.harvested"
                    ]
                ),
                StageConfiguration(
                    next="stump",
                    conditions=["calendar.season == constants.Seasons.WINTER.value"]
                )
            ],
            "stump": [
                StageConfiguration(
                    next="sprout",
                    conditions=[
                        "calendar.season == constants.Seasons.SPRING.value",
                        "calendar.cycle == constants.Cycles.ONSET.value",
                        "calendar.period == 0",
                        "resource.retention >= 10.0"
                    ]
                )
            ]
        },
        "perennial": {
            "sapling": [
                StageConfiguration(
                    next="bush",
                    conditions=[
                        "calendar.season == constants.Seasons.SPRING.value",
                        "calendar.cycle == constants.Cycles.PEAK.value",
                        "resource.retention >= 15.0"
                    ]
                )
            ],
            "bush": [
                StageConfiguration(
                    next="branch",
                    conditions=[
                        "calendar.season == constants.Seasons.SPRING.value",
                        "calendar.cycle == constants.Cycles.DECLINE.value",
                        "resource.retention >= 20.0"
                    ]
                )
            ],
            "branch": [
                StageConfiguration(
                    next="adult",
                    conditions=[
                        "calendar.season == constants.Seasons.SUMMER.value",
                        "calendar.cycle == constants.Cycles.ONSET.value",
                        "resource.retention >= 25.0"
                    ]
                )
            ],
            "adult": [
                StageConfiguration(
                    next="healthy",
                    conditions=[
                        "calendar.season == constants.Seasons.SUMMER.value",
                        "calendar.cycle == constants.Cycles.PEAK.value",
                        "resource.retention >= 25.0"
                    ]
                )
            ],
            "vibrant": [
                StageConfiguration(
                    next="healthy",
                    conditions=[
                        "calendar.season == constants.Seasons.SUMMER.value",
                        "resource.retention >= 20.0"
                    ]
                ),
                StageConfiguration(
                    next="dying",
                    conditions=["resource.retention < 5.0"]
                )
            ],
            "healthy": [
                StageConfiguration(
                    next="abscise",
                    conditions=[
                        "calendar.season == constants.Seasons.AUTUMN.value",
                        "resource.retention >= 15.0"
                    ]
                ),
                StageConfiguration(
                    next="dying",
                    conditions=["resource.retention < 5.0"]
                )
            ],
            "abscise": [
                StageConfiguration(
                    next="snowcapt",
                    conditions=[
                        "calendar.season == constants.Seasons.WINTER.value",
                        "resource.retention >= 10.0"
                    ]
                ),
                StageConfiguration(
                    next="dying",
                    conditions=["resource.retention < 5.0"]
                )
            ],
            "snowcapt": [
                StageConfiguration(
                    next="vibrant",
                    conditions=[
                        "calendar.season == constants.Seasons.SPRING.value",
                        "resource.retention >= 15.0"
                    ]
                ),
                StageConfiguration(
                    next="dying",
                    conditions=["resource.retention < 5.0"]
                )
            ],
            "dying": [
                StageConfiguration(
                    next="vibrant",
                    conditions=[
                        "calendar.season == constants.Seasons.SPRING.value",
                        "resource.retention >= 20.0"
                    ]
                ),
                StageConfiguration(
                    next="healthy",
                    conditions=[
                        "calendar.season == constants.Seasons.SUMMER.value",
                        "resource.retention >= 20.0"
                    ]
                ),
                StageConfiguration(
                    next="dead",
                    conditions=[
                        "calendar.season == constants.Seasons.AUTUMN.value",
                        "resource.retention < 5.0"
                    ]
                )
            ],
            "dead": [
                StageConfiguration(
                    next="stump",
                    conditions=["calendar.season == constants.Seasons.WINTER.value"]
                )
            ],
            "stump": [
                StageConfiguration(
                    next="sapling",
                    conditions=[
                        "calendar.season == constants.Seasons.SPRING.value",
                        "calendar.cycle == constants.Cycles.ONSET.value",
                        "calendar.period == 0",
                        "resource.retention >= 15.0"
                    ]
                )
            ]
        }
    }