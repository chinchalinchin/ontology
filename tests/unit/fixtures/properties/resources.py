"""
# Ontology: tests.unit.fixtures.properties.resources
Mock Geography Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Lifespans
)
from app.models.properties import (
    ResourceProperties,
    ResourcePropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Hitbox, 
    Position
)


@pytest.fixture
def mock_resource_properties() -> ResourcePropertyInstances:
    return ResourcePropertyInstances(
        trees={
            "deciduous": ResourceProperties(
                dimensions=Dimensions(w=94, l=137),
                lifespan=Lifespans.PERENNIAL.value,
                loot="wood",
                mass=0,
                hitboxes={
                    "sapling": [],
                    "bush": [Hitbox(Position(36, 114), Dimensions(22, 20))],
                    "branch": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "adult": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "vibrant": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "healthy": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "abscise": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "snowcapt": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "dying": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "dead": [Hitbox(Position(36, 110), Dimensions(22, 24))],
                    "stump": [Hitbox(Position(30, 115), Dimensions(34, 18))]
                }
            )
        },
        crops={
            "lettuce": ResourceProperties(
                dimensions=Dimensions(w=32, l=22),
                lifespan=Lifespans.ANNUAL.value,
                loot="lettuce",
                mass=0,
                hitboxes={
                    "sprout": [],
                    "growth": [],
                    "stalk": [Hitbox(Position(6, 10), Dimensions(20, 12))],
                    "bloom": [Hitbox(Position(4, 6), Dimensions(24, 16))],
                    "stump": []
                }
            )
        }
    )