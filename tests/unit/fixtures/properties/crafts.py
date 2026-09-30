"""
# Ontology: tests.unit.fixtures.properties

Mock Asset Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    Cost,
    CraftProperties,
    CraftPropertyInstances
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Hitbox
)


@pytest.fixture
def mock_craft_properties() -> CraftPropertyInstances:
    return CraftPropertyInstances(
        struts = {
            'frame-brick': CraftProperties(
                dimensions=Dimensions(w=96, l=190),
                cost=[
                    Cost(item="stone", quantity=10)
                ],
                mass=0
            ),
            'frame-wood': CraftProperties(
                dimensions=Dimensions(w=100, l=100),
                cost=[
                    Cost(item="wood", quantity=10)
                ],
                mass=0
            ),
            'wall-blue': CraftProperties(
                dimensions=Dimensions(w=128, l=96),
                cost=[
                    Cost(item="stone", quantity=5)
                ],
                mass=0
            ),
            'floor-wood': CraftProperties(
                dimensions=Dimensions(w=128, l=96),
                cost=[
                    Cost(item="wood", quantity=10)
                ],
                mass=0
            ),
            'strut-castle': CraftProperties(
                dimensions=Dimensions(w=222, l=133), 
                cost=[], 
                mass=0
            ),
            'strut-wall':  CraftProperties(
                dimensions=Dimensions(w=128, l=96), 
                cost=[], 
                mass=0
            ),
            'strut-floor': CraftProperties(
                dimensions=Dimensions(w=128, l=96), 
                cost=[], 
                mass=0
            )
        },
        bridges = {
            'wood-bridge': CraftProperties(
                dimensions=Dimensions(w=32, l=32),
                cost=[Cost(item="wood", quantity=2)],
                mass=-1,
                hitboxes=[Hitbox(Position(0, 8), Dimensions(32, 16))]
            ),
        }
    )