"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.objects

# Ontology: Tests - tests.unit.fixtures.properties.objects

Mock Object Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    LayerProjections,
    Materials,
    Organics,
)
from app.models.properties import (
    Material,
    ObjectProperties,
    ObjectPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Hitbox,
)


@pytest.fixture
def mock_object_properties() -> ObjectPropertyInstances:
    geologics = Material(genus=Materials.GEOLOGICS.value)
    organics = Material(genus=Materials.ORGANICS.value)
    metallics = Material(genus=Materials.METALLICS.value)
    chromatics_wood = Material(
        genus=Materials.CHROMATICS.value,
        host=Organics.WOOD.value,
    )
    chromatics_cotton = Material(
        genus=Materials.CHROMATICS.value,
        host=Organics.COTTON.value,
    )

    return ObjectPropertyInstances(
        chests={
            "trunk": ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=10,
                count=2,
                material=metallics,
                hitboxes=None,
            ),
            "container": ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=5,
                count=2,
                material=organics,
                hitboxes=None,
            ),
        },
        crates={
            "box": ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=1,
                count=1,
                material=organics,
                hitboxes=None,
            ),
        },
        doors={
            "panel": ObjectProperties(
                dimensions=Dimensions(w=32, l=48),
                mass=-1,
                count=1,
                priority=1,
                material=chromatics_wood,
                hitboxes={
                    LayerProjections.IN.value: [
                        Hitbox(Position(0, 12), Dimensions(32, 36)),
                    ],
                    LayerProjections.OUT.value: [
                        Hitbox(Position(0, 0), Dimensions(32, 16)),
                    ],
                },
            ),
            "dutch": ObjectProperties(
                dimensions=Dimensions(w=32, l=48),
                mass=-1,
                count=1,
                priority=1,
                material=chromatics_wood,
                hitboxes={
                    LayerProjections.IN.value: [
                        Hitbox(Position(0, 0), Dimensions(32, 36)),
                    ],
                    LayerProjections.OUT.value: [
                        Hitbox(Position(0, 12), Dimensions(32, 16)),
                    ],
                },
            ),
            "pivot": ObjectProperties(
                dimensions=Dimensions(w=32, l=48),
                mass=-1,
                count=1,
                priority=1,
                material=chromatics_wood,
                hitboxes={
                    LayerProjections.IN.value: [
                        Hitbox(Position(0, 12), Dimensions(32, 36)),
                    ],
                    LayerProjections.OUT.value: [
                        Hitbox(Position(0, 0), Dimensions(32, 16)),
                    ],
                },
            ),
        },
        gates={
            "postern": ObjectProperties(
                dimensions=Dimensions(w=64, l=64),
                mass=0,
                count=2,
                material=geologics,
                hitboxes=None,
            ),
        },
        obstacles={
            "gray-rock-00": ObjectProperties(
                mass=0,
                dimensions=Dimensions(w=56, l=56),
                hitboxes=None,
            ),
            "gray-rock-01": ObjectProperties(
                mass=0,
                dimensions=Dimensions(w=56, l=57),
                hitboxes=None,
            ),
        },
        plates={
            "stone-switch": ObjectProperties(
                mass=-1,
                dimensions=Dimensions(w=15, l=14),
                count=2,
                hitboxes=None,
            ),
        },
        signs={
            "plaque": ObjectProperties(
                dimensions=Dimensions(w=24, l=24),
                mass=-1,
                count=1,
                material=geologics,
                hitboxes=None,
            ),
            "poster": ObjectProperties(
                dimensions=Dimensions(w=30, l=30),
                mass=-1,
                count=1,
                material=chromatics_cotton,
                hitboxes=None,
            ),
            "scroll": ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=-1,
                count=1,
                material=chromatics_cotton,
                hitboxes=None,
            ),
        },
    )