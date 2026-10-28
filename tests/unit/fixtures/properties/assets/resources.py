"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.resources

# Ontology: tests.unit.fixtures.properties.resources

Mock Resource Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import Lifespans
from app.models.properties import (
    ResourceProperties,
    ResourcePropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position,
)


@pytest.fixture
def mock_resource_properties() -> ResourcePropertyInstances:
    trunk_hitbox = [Hitbox(Position(36, 110), Dimensions(22, 24))]
    crop_hitboxes = {
        "sprout": None,
        "growth": None,
        "stalk": None,
        "bloom": None,
        "stump": None,
    }

    return ResourcePropertyInstances(
        trees={
            "deciduous": ResourceProperties(
                dimensions=Dimensions(w=94, l=137),
                lifespan=Lifespans.PERENNIAL.value,
                loot="wood",
                mass=0,
                hitboxes={
                    "sapling": [Hitbox(Position(42, 122), Dimensions(10, 12))],
                    "bush": [Hitbox(Position(36, 114), Dimensions(22, 20))],
                    "branch": trunk_hitbox,
                    "adult": trunk_hitbox,
                    "vibrant": trunk_hitbox,
                    "healthy": trunk_hitbox,
                    "abscise": trunk_hitbox,
                    "snowcapt": trunk_hitbox,
                    "dying": trunk_hitbox,
                    "dead": trunk_hitbox,
                    "stump": trunk_hitbox,
                },
            ),
        },
        crops={
            "lettuce": ResourceProperties(
                dimensions=Dimensions(w=32, l=22),
                lifespan=Lifespans.ANNUAL.value,
                loot="lettuce",
                mass=0,
                hitboxes=dict(crop_hitboxes),
            ),
            "maize": ResourceProperties(
                dimensions=Dimensions(w=32, l=64),
                lifespan=Lifespans.ANNUAL.value,
                loot="maize",
                mass=0,
                hitboxes=dict(crop_hitboxes),
            ),
        },
        ore={
            "gold": ResourceProperties(
                dimensions=Dimensions(w=32, l=32),
                lifespan=Lifespans.CENTENNIAL.value,
                loot="gold-ore",
                mass=0,
                hitboxes={
                    "trace": None,
                    "deposit": None,
                    "nugget": None,
                    "vein": None,
                    "crystal": None,
                },
            ),
        },
    )