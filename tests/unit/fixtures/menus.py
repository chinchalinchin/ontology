"""
# Ontology: tests.unit.conftest
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import ( 
    Bindings,
    Shortcuts,
)
from app.models.config import (
    MenuNode,
    GizmoParameters,
    MenuBinding,
)
from app.models.state import (
    CollectionState,
)


# -----------------------------------------------------------------------------
# -------------------------------------------------------- MOCK MENU COMPONENTS
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_gizmo_node():
    return MenuNode(
        id="weapons",
        name="inventory-pack-grid",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(
            schema=Bindings.COLLECTION.value,
            target={"source": "context.inventory.pack"}
        ),
        parameters=GizmoParameters(
            capacity=8,
            columns=4,
            pane="transparent-slot",
            button="slot",
            gap=5
        )
    )


@pytest.fixture
def mock_collection_state():
    return CollectionState(
        collection_function=lambda: ["shortsword", "dagger", "buckler"],
        capacity=8,
        columns=4,
        offset=0
    )