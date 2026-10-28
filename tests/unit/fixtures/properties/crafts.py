"""
@test.fixtures

# Ontology: tests.unit.fixtures.properties.crafts

Mock Craft Property fixtures aligned with src/assets/crafts/.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Blueprints,
    Directions,
    Materials,
    Organics,
    Orientations,
)
from app.models.properties import (
    CraftProperties,
    CraftPropertyInstances,
    Material,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Hitbox,
)


@pytest.fixture
def mock_craft_properties() -> CraftPropertyInstances:
    geologics = Material(genus=Materials.GEOLOGICS.value)
    organics = Material(genus=Materials.ORGANICS.value)
    chromatics_wood = Material(
        genus=Materials.CHROMATICS.value,
        host=Organics.WOOD.value,
    )
    chromatics_cotton = Material(
        genus=Materials.CHROMATICS.value,
        host=Organics.COTTON.value,
    )

    return CraftPropertyInstances(
        bridges={
            "arch": CraftProperties(
                dimensions=Dimensions(w=80, l=103),
                material=geologics,
                blueprints=Blueprints.ORIENTATIONS.value,
                mass=-1,
                hitboxes=None,
            ),
            "suspension": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                material=organics,
                blueprints=Blueprints.ORIENTATIONS.value,
                mass=-1,
                hitboxes=None,
            ),
        },
        stairs={
            "steps": CraftProperties(
                dimensions=Dimensions(w=64, l=96),
                mass=-1,
                material=geologics,
                blueprints=Blueprints.INCLINES.value,
                hitboxes={
                    Directions.UP.value: [
                        Hitbox(Position(0, 0), Dimensions(32, 96)),
                    ],
                    Directions.LEFT.value: [
                        Hitbox(Position(0, 0), Dimensions(64, 32)),
                    ],
                    Directions.RIGHT.value: [
                        Hitbox(Position(0, 0), Dimensions(64, 32)),
                    ],
                },
            ),
        },
        struts={
            # ---- BUILDINGS
            "home": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=geologics,
                blueprints=Blueprints.BUILDINGS.value,
            ),
            "mansion": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=geologics,
                blueprints=Blueprints.BUILDINGS.value,
            ),
            "shack": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=organics,
                blueprints=Blueprints.BUILDINGS.value,
            ),
            "store": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=geologics,
                blueprints=Blueprints.BUILDINGS.value,
            ),
            "suburb": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=chromatics_wood,
                blueprints=Blueprints.BUILDINGS.value,
            ),
            # ---- CORRIDORS
            "avenue": CraftProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=0,
                hitboxes=None,
                material=geologics,
                blueprints=Blueprints.CORRIDORS.value,
            ),
            "carpet": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=chromatics_cotton,
                blueprints=Blueprints.CORRIDORS.value,
            ),
            "hallway": CraftProperties(
                dimensions=Dimensions(w=96, l=96),
                mass=0,
                hitboxes=None,
                material=chromatics_wood,
                blueprints=Blueprints.CORRIDORS.value,
            ),
            # ---- COLUMNS
            "pillar": CraftProperties(
                dimensions=Dimensions(w=16, l=32),
                mass=0,
                hitboxes=None,
                material=geologics,
                blueprints=Blueprints.COLUMNS.value,
            ),
            "tower": CraftProperties(
                dimensions=Dimensions(w=64, l=64),
                mass=0,
                hitboxes=None,
                material=geologics,
                blueprints=Blueprints.COLUMNS.value,
            ),
            # ---- RAILINGS
            "crenellation": CraftProperties(
                dimensions=Dimensions(w=32, l=32),
                mass=0,
                material=geologics,
                blueprints=Blueprints.ORIENTATIONS.value,
                hitboxes={
                    Orientations.HORIZONTAL.value: [
                        Hitbox(Position(0, 0), Dimensions(32, 10)),
                    ],
                    Orientations.VERTICAL.value: [
                        Hitbox(Position(0, 0), Dimensions(9, 32)),
                    ],
                },
            ),
            # ---- CARPENTRY
            "bed": CraftProperties(
                dimensions=Dimensions(w=71, l=74),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DIRECTIONS.value,
                hitboxes=None,
            ),
            "chair": CraftProperties(
                dimensions=Dimensions(w=26, l=32),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DIRECTIONS.value,
                hitboxes=None,
            ),
            "sofa": CraftProperties(
                dimensions=Dimensions(w=64, l=64),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DIRECTIONS.value,
                hitboxes=None,
            ),
            "throne": CraftProperties(
                dimensions=Dimensions(w=32, l=75),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DIRECTIONS.value,
                hitboxes=None,
            ),
            # ---- DECOR
            "banner": CraftProperties(
                dimensions=Dimensions(w=32, l=64),
                mass=-1,
                material=chromatics_cotton,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "curtain": CraftProperties(
                dimensions=Dimensions(w=32, l=94),
                mass=-1,
                material=chromatics_cotton,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "dresser": CraftProperties(
                dimensions=Dimensions(w=32, l=53),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "fireplace": CraftProperties(
                dimensions=Dimensions(w=72, l=70),
                mass=0,
                material=geologics,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "palette": CraftProperties(
                dimensions=Dimensions(w=63, l=58),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "painting": CraftProperties(
                dimensions=Dimensions(w=31, l=39),
                mass=-1,
                material=chromatics_cotton,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "portrait": CraftProperties(
                dimensions=Dimensions(w=29, l=49),
                mass=-1,
                material=chromatics_cotton,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "table": CraftProperties(
                dimensions=Dimensions(w=63, l=54),
                mass=0,
                material=chromatics_wood,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
            "taxidermy": CraftProperties(
                dimensions=Dimensions(w=31, l=31),
                mass=-1,
                material=chromatics_wood,
                blueprints=Blueprints.DECOR.value,
                hitboxes=None,
            ),
        },
    )