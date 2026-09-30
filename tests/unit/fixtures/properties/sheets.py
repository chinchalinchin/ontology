"""
# Ontology: tests.unit.fixtures.properties.sheets

Mock Sheet Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Actions,
    Directions,
)
from app.models.properties import (
    Action,
    Direction,
    SheetProperties,
    SheetPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Hitbox
)

@pytest.fixture
def mock_sheet_properties() -> SheetPropertyInstances:
    lpc_hitbox = Hitbox(Position(21, 23), Dimensions(22, 21))
    weapon_hitbox = Hitbox(Position(10, 15), Dimensions(20, 25))

    return SheetPropertyInstances(
        sprites = {
            "player": SheetProperties(
                dimensions = Dimensions(w=64, l=64),
                mass = 7,
                hitboxes = [ lpc_hitbox ]
            ),
            'jasilynn':  SheetProperties(
                dimensions =Dimensions(w=64, l=64),
                mass = 10,
                hitboxes = [ lpc_hitbox ]
            ),
            'sprite':  SheetProperties(
                dimensions = Dimensions(w=64, l=64),
                mass = 10,
                hitboxes = [lpc_hitbox]
            )
        },
        weapons = {
            'shortsword': SheetProperties(
                dimensions = Dimensions(64, 64),
                attackboxes = {
                    "slash-right-3": [ weapon_hitbox ] 
                },
                actions = {
                    Actions.SLASH.value: Action(
                        count = 6,
                        directions = {
                            Directions.UP.value: Direction(row=12),
                            Directions.LEFT.value: Direction(row=13),
                            Directions.DOWN.value: Direction(row=14),
                            Directions.RIGHT.value: Direction(row=15)
                        }
                    )
                }
            )
        }
    )
