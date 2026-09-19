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
from app.config.enums import (
    AssetInstances,
    Layouts,
    Alignments,
    Statuses,
    Selections,
    Bindings,
    Shortcuts
)


def test_fabricator_expand_collection_dimensions_and_subtrees(widget_properties):
    """
    Verifies that a valid collection gizmo correctly calculates macro dimensions,
    splits capacity into row panes, and synthesizes child button and icon apertures.
    """
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
    assert expanded.bind.target["source"] == "context.inventory.pack"
    assert expanded.bind.target["capacity"] == "8"
    assert expanded.bind.target["columns"] == "4"

    params = expanded.parameters
    assert isinstance(params, PaneParameters)
    assert params.dimensions.w == 175  # 4 * 40 + (4 - 1) * 5
    assert params.dimensions.l == 85   # 2 * 40 + (2 - 1) * 5
    assert len(params.children) == 2   # 2 rows

    row_0 = params.children[0]
    assert row_0.instance == AssetInstances.PANES.value
    assert row_0.parameters.layout == Layouts.DOCK
    assert row_0.parameters.dimensions.w == 175
    assert row_0.parameters.dimensions.l == 40
    assert len(row_0.parameters.children) == 4

    slot_0_pane = row_0.parameters.children[0]
    assert slot_0_pane.parameters.layout == Layouts.OVERLAY
    assert slot_0_pane.parameters.dimensions.w == 40
    assert slot_0_pane.parameters.dimensions.l == 40
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


def test_fabricator_expand_collection_uneven_capacity(widget_properties):
    """
    Verifies that capacity not evenly divisible by columns generates the correct
    number of slots in the trailing row.
    """
    node = MenuNode(
        id="weapons",
        name="uneven-grid",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(
            schema=Bindings.COLLECTION.value,
            target={"collection": "context.inventory.pack"}
        ),
        parameters=GizmoParameters(
            capacity=5,
            columns=4,
            gap=5,
            pane="transparent-slot",
            button="slot"
        )
    )

    expanded = Fabricator.expand(node, context={}, properties=widget_properties)
    params = expanded.parameters

    assert len(params.children) == 2
    row_0 = params.children[0]
    row_1 = params.children[1]

    assert len(row_0.parameters.children) == 4
    assert len(row_1.parameters.children) == 1

    last_slot = row_1.parameters.children[0]
    btn, icon = last_slot.parameters.children
    assert btn.name == "uneven-grid-slot-4"
    assert btn.bind.target["index"] == "4"
    assert icon.name == "uneven-grid-icon-4"
    assert icon.bind.target["index"] == "4"


def test_fabricator_expand_missing_binding_raises_value_error(widget_properties):
    """
    Verifies that declaring a gizmo without a bind block raises ValueError.
    """
    node = MenuNode(
        id="weapons",
        name="no-binding-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=None,
        parameters=GizmoParameters(
            capacity=8,
            columns=4,
            pane="transparent-slot",
            button="slot"
        )
    )
    with pytest.raises(ValueError, match="declared without a binding schema"):
        Fabricator.expand(node, context={}, properties=widget_properties)


def test_fabricator_expand_empty_schema_raises_value_error(widget_properties):
    """
    Verifies that declaring a gizmo with an empty binding schema raises ValueError.
    """
    node = MenuNode(
        id="weapons",
        name="empty-schema-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(schema=""),
        parameters=GizmoParameters(
            capacity=8,
            columns=4,
            pane="transparent-slot",
            button="slot"
        )
    )
    with pytest.raises(ValueError, match="declared without a binding schema"):
        Fabricator.expand(node, context={}, properties=widget_properties)


def test_fabricator_expand_unsupported_schema_raises_not_implemented(widget_properties):
    """
    Verifies that passing an unregistered gizmo schema raises NotImplementedError.
    """
    node = MenuNode(
        id="weapons",
        name="unsupported-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(schema="unregistered_schema"),
        parameters=GizmoParameters(
            capacity=8,
            columns=4,
            pane="transparent-slot",
            button="slot"
        )
    )
    with pytest.raises(NotImplementedError, match="Unsupported gizmo schema 'unregistered_schema'"):
        Fabricator.expand(node, context={}, properties=widget_properties)


def test_fabricator_expand_collection_invalid_parameters_type(widget_properties):
    """
    Verifies that a collection schema receiving non-GizmoParameters raises TypeError.
    """
    node_none = MenuNode(
        id="weapons",
        name="none-params-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(schema=Bindings.COLLECTION.value),
        parameters=None
    )
    with pytest.raises(TypeError, match="expects GizmoParameters, got <class 'NoneType'>"):
        Fabricator.expand(node_none, context={}, properties=widget_properties)

    node_wrong = MenuNode(
        id="weapons",
        name="wrong-params-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(schema=Bindings.COLLECTION.value),
        parameters=PaneParameters()
    )
    with pytest.raises(TypeError, match="expects GizmoParameters"):
        Fabricator.expand(node_wrong, context={}, properties=widget_properties)


def test_fabricator_extract_source_path_variants():
    """
    Verifies source path extraction across string, dictionary, and empty targets.
    """
    bind_str = MenuBinding(schema=Bindings.COLLECTION.value, target="context.player.bag")
    assert Fabricator._extract_source_path(bind_str) == "context.player.bag"

    bind_src = MenuBinding(schema=Bindings.COLLECTION.value, target={"source": "context.player.pouch"})
    assert Fabricator._extract_source_path(bind_src) == "context.player.pouch"

    bind_col = MenuBinding(schema=Bindings.COLLECTION.value, target={"collection": "context.chest.loot"})
    assert Fabricator._extract_source_path(bind_col) == "context.chest.loot"

    bind_empty = MenuBinding(schema=Bindings.COLLECTION.value, target={"other": "data"})
    assert Fabricator._extract_source_path(bind_empty) == ""

    assert Fabricator._extract_source_path(MenuBinding(schema=Bindings.COLLECTION.value, target=None)) == ""
    assert Fabricator._extract_source_path(None) == ""