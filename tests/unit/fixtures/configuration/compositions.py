"""
# Ontology: tests.unit.fixtures.configuration.compositions

Mock Composition Configuration fixtures
"""
# External Libraries
import pytest


from app.models.config import (
    # ------ COMPOSITIONS
    CompositionConfiguration, 
    CompositionPseudoState, 
)
from app.models.state import (
    # -------- SCHEMA
    StateSchema, 
    # -------- INSTANCES
    ObjectStateInstances, 
    CraftStateInstances,
    # -------- MODELS
    DoorState,
    PropertyState
)
# Cython Libraries
from libs.core.models import Position


# --------------------------------------------------------------------------
# ------------------------------------------------------ MOCK CONFIGURATIONS
# --------------------------------------------------------------------------

@pytest.fixture
def mock_composition_configuration() -> CompositionConfiguration:
    return {
        "test-house": CompositionConfiguration(
            root=CompositionPseudoState(
                strut=PropertyState(
                    id="frame-wood", 
                    name="base_house"
                ),
                components=StateSchema(
                    objects=ObjectStateInstances(
                        doors=[
                            DoorState(
                                id="door-front",
                                name="entrance",
                                position=Position(x=20, y=20),
                                out=Position(x=5, y=5),
                                outlayer="bind(root.layer)"
                            )
                        ]
                    )
                )
            ),
            branches=[
                CompositionPseudoState(
                    strut=PropertyState(
                        id="wall-blue", 
                        name="interior",
                        position=Position(x=10, y=10),
                        owner="bind(parent.owner)"
                    ),
                    components=StateSchema()
                )
            ]
        ),
        'brick-house': CompositionConfiguration(
            root=CompositionPseudoState(
                strut=PropertyState(id="frame-brick", name="house"),
                components=StateSchema(
                    objects=ObjectStateInstances(
                        doors=[
                            DoorState(
                                id="door-house",
                                name="entrance",
                                layer="0",
                                outlayer="brick-house-compose-layer",
                                position=Position(x=32, y=118),
                                out=Position(x=82, y=143)
                            )
                        ]
                    )
                )
            ),
            branches=[
                CompositionPseudoState(
                    strut=PropertyState(
                        id="wall-blue",
                        name="house-interior",
                        layer="brick-house-compose-layer",
                        position=Position(x=0, y=0),
                        owner="bind(root.owner)"
                    ),
                    components=StateSchema(
                        crafts=CraftStateInstances(
                            struts=[
                                PropertyState(
                                    id="floor-wood",
                                    name="house-floor",
                                    layer="brick-house-compose-layer",
                                    position=Position(x=0, y=96),
                                    owner="bind(root.owner)"
                                )
                            ]
                        ),
                        objects=ObjectStateInstances(
                            doors=[
                                DoorState(
                                    id="door-shadow",
                                    name="house-doorframe",
                                    layer="brick-house-compose-layer",
                                    outlayer="bind(root.layer)",
                                    position=Position(x=47, y=142),
                                    out=Position(x=43, y=163)
                                )
                            ]
                        )
                    )
                )
            ]
        )
    }