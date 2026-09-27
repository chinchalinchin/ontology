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
# --------------------------------------------------------------- MOCK BINDINGS
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_library_bind():
    return MenuBinding(
        schema = Bindings.LIBRARY.value,
        target = { 'plot': 'context.plot' }
    )


@pytest.fixture
def mock_meter_bind():
    return MenuBinding(
        schema = Bindings.METER.value, 
        target = { 'meter': 'context.health' }
    )


@pytest.fixture
def mock_icon_bind():
    return MenuBinding(
        schema = Bindings.ICON.value,
        target = { 'icon': 'context.item' }
    )


@pytest.fixture
def mock_select_bind():
    return MenuBinding(
        schema = Bindings.SELECT.value,
        target = { 'selection': 'scrollup', 'selector': 'my_page' }
    )


@pytest.fixture
def mock_collection_bind():
    return MenuBinding(
        schema = Bindings.COLLECTION.value,
        target = { 'source': 'context.inventory.pack' }
    )


@pytest.fixture
def mock_aperture_bind():
    return MenuBinding(
        schema = Bindings.APERTURE.value,
        target = { 'selector': 'inventory-pack-grid', 'index': '0' }
    )

@pytest.fixture
def mock_aperture_bind_alt():
    return MenuBinding(
        schema = Bindings.APERTURE,
        target = { 'selector': 'inventory-pack-grid', 'index': '5' }
    )

# -----------------------------------------------------------------------------
# ---------------------------------------------------------- MOCK CONFIGURATION
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_gizmo_node(mock_collection_bind):
    return MenuNode(
        id = "weapons",
        name = "inventory-pack-grid",
        instance = Shortcuts.GIZMOS.value,
        bind = mock_collection_bind,
        parameters = GizmoParameters(
            capacity = 8,
            columns = 4,
            pane = "transparent-slot",
            button = "slot",
            gap = 5
        )
    )


# -----------------------------------------------------------------------------
# ----------------------------------------------------------------- MOCK STATES
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_collection_state():
    return CollectionState(
        collection_function=lambda: ["shortsword", "dagger", "buckler"],
        capacity=8,
        columns=4,
        offset=0
    )