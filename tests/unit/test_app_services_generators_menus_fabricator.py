"""
# Ontology: tests.unit.test_app_services_generators_menus_fabricator
"""
import pytest
from app.services.generators.menus.fabricator import Fabricator
from app.models.config.menus import (
    MenuNode,
    GizmoParameters,
    PaneParameters,
    ButtonParameters,
    MenuBinding
)
from app.models.properties import WidgetPropertyInstances, WidgetProperties
from app.config.enums import (
    AssetInstances,
    Layouts,
    Alignments,
    Statuses,
    Selections,
    Bindings,
    Shortcuts
)
from libs.core.models import Dimensions


@pytest.fixture
def widget_properties():
    return WidgetPropertyInstances(
        panes={"transparent-slot": WidgetProperties(dimensions=Dimensions(w=40, l=40))},
        buttons={"slot": WidgetProperties(dimensions=Dimensions(w=40, l=40))}
    )


def test_fabricator_expand_dimensions_and_subtrees(widget_properties):
    node = MenuNode(
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
            gap=5,
            pane="transparent-slot",
            button="slot"
        )
    )

    expanded = Fabricator.expand(node, context={}, properties=widget_properties)

    assert expanded is not None
    assert expanded.id == "transparent-slot"
    assert expanded.name == "inventory-pack-grid"
    assert expanded.instance == AssetInstances.PANES.value
    assert expanded.bind.schema == Bindings.COLLECTION.value

    params = expanded.parameters
    assert isinstance(params, PaneParameters)
    assert params.dimensions.w == 175  # 4 * 40 + (4 - 1) * 5
    assert params.dimensions.l == 85   # 2 * 40 + (2 - 1) * 5
    assert len(params.children) == 2   # 2 rows

    row_0 = params.children[0]
    assert row_0.instance == AssetInstances.PANES.value
    assert row_0.parameters.layout == Layouts.DOCK
    assert len(row_0.parameters.children) == 4  # 4 slots in row

    slot_0_pane = row_0.parameters.children[0]
    assert slot_0_pane.parameters.layout == Layouts.OVERLAY
    button_node, icon_node = slot_0_pane.parameters.children

    # Button node assertion
    assert button_node.instance == AssetInstances.BUTTONS.value
    assert button_node.id == "slot"
    assert button_node.name == "inventory-pack-grid-slot-0"
    assert button_node.bind.schema == Bindings.SELECT.value
    assert button_node.bind.target["selection"] == Selections.SLOT.value
    assert button_node.bind.target["selector"] == "inventory-pack-grid"
    assert button_node.bind.target["index"] == "0"
    assert button_node.parameters.status == Statuses.IDLE

    # Icon aperture assertion
    assert icon_node.instance == AssetInstances.ICONS.value
    assert icon_node.id == "weapons"
    assert icon_node.name == "inventory-pack-grid-icon-0"
    assert icon_node.bind.schema == Bindings.APERTURE.value
    assert icon_node.bind.target["selector"] == "inventory-pack-grid"
    assert icon_node.bind.target["index"] == "0"


def test_fabricator_expand_invalid_parameters(widget_properties):
    node = MenuNode(
        id="weapons",
        name="invalid-gizmo",
        instance=Shortcuts.GIZMOS.value,
        parameters=None
    )
    expanded = Fabricator.expand(node, context={}, properties=widget_properties)
    assert expanded is None