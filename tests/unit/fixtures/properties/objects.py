"""
# Ontology: tests.unit.fixtures.properties.objects

Mock Object Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    ObjectProperties,
    ObjectPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Hitbox
)


@pytest.fixture
def mock_object_properties() -> ObjectPropertyInstances:
    return ObjectPropertyInstances(
        doors = {
            "door-front": ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                hitboxes = [Hitbox(Position(0, 0), Dimensions(32, 32))],
                mass = -1
            ),
            'door-shadow': ObjectProperties(
                dimensions=Dimensions(w=32, l=48),
                mass = -1
            ),
            'door-house': ObjectProperties(
                dimensions=Dimensions(w=32, l=48),
                mass = -1
            )
        },
        crates = {
            'wood-crate': ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=5
            ) 
        },
        rafts = {
            'wood-raft': ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=5
            )
        },
        gates = {
            'castle-gate': ObjectProperties(
                dimensions=Dimensions(w=32, l=32), 
                mass=0
            )
        },
        chests = {
            'wood-chest': ObjectProperties(
                dimensions=Dimensions(w=64, l=32),
                hitboxes=[Hitbox(Position(0, 0), Dimensions(64, 32))],
                count=2,
                mass=10
            )
        },
        plates = {
            'pressure-plate': ObjectProperties(
                dimensions=Dimensions(w=32, l=32),
                hitboxes=[Hitbox(Position(0, 0), Dimensions(32, 32))],
                count=2,
                mass=-1
            )
        },
    )