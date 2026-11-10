"""
@domain.test
@test.unit
@app.service
@app.menu
@menu.gizmo

# Ontology: Tests - tests.unit.app.services.generators.menu.test_fabricator

Unit tests for the Fabricator service.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.config.menus import (
    ApertureTarget,
    CollectionTarget,
    GizmoParameters,
    MenuBinding,
    MenuNode,
    PaneParameters,
    SelectTarget,
)
from app.services.generators.menus.fabricator import Fabricator
from app.static.semantics import (
    AssetInstances,
    Bindings,
    Layouts,
    Selections,
    Shortcuts,
    Statuses,
)

# Cython Libraries
from libs.core.models import Scale

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
    pytest.mark.app_menu,
    pytest.mark.menu_gizmo,
]

# ---------------------------------------------------------------------------


def test_fabricator_expand_collection_scales_and_subtrees(
    mock_fabricator: Fabricator,
    mock_gizmo_node: MenuNode,
    mock_menu_context,
):
    """
    Verifies that a valid collection gizmo subdivides fractional Scale dimensions
    across row and slot panes and synthesizes button and icon aperture nodes.
    """
    context = mock_menu_context()
    expanded = mock_fabricator.expand(mock_gizmo_node, context=context)

    assert expanded.id == "transparent"
    assert expanded.name == "inventory-pack-grid"
    assert expanded.instance == AssetInstances.PANES.value
    assert expanded.bind.schema == Bindings.COLLECTION.value
    assert isinstance(expanded.bind.target, CollectionTarget)
    assert expanded.bind.target.source == "context.inventory.pack"
    assert expanded.bind.target.capacity == 8
    assert expanded.bind.target.columns == 4

    params = expanded.parameters
    assert isinstance(params, PaneParameters)
    assert params.dimensions.pw == pytest.approx(0.60)
    assert params.dimensions.pl == pytest.approx(0.30)
    assert len(params.children) == 2  # 8 slots / 4 columns = 2 rows

    row_0 = params.children[0]
    assert row_0.instance == AssetInstances.PANES.value
    assert row_0.parameters.layout == Layouts.DOCK.value
    assert row_0.parameters.dimensions.pw == pytest.approx(0.60)
    assert row_0.parameters.dimensions.pl == pytest.approx(0.15)
    assert len(row_0.parameters.children) == 4

    slot_0_pane = row_0.parameters.children[0]
    assert slot_0_pane.parameters.layout == Layouts.OVERLAY.value
    assert slot_0_pane.parameters.dimensions.pw == pytest.approx(0.15)
    assert slot_0_pane.parameters.dimensions.pl == pytest.approx(0.15)
    button_node, icon_node = slot_0_pane.parameters.children

    assert button_node.instance == AssetInstances.BUTTONS.value
    assert button_node.id == "slot"
    assert button_node.name == "inventory-pack-grid-slot-0"
    assert button_node.bind.schema == Bindings.SELECT.value
    assert isinstance(button_node.bind.target, SelectTarget)
    assert button_node.bind.target.selection == Selections.SLOT.value
    assert button_node.bind.target.selector == "inventory-pack-grid"
    assert button_node.bind.target.index == 0
    assert button_node.parameters.status == Statuses.IDLE.value

    assert icon_node.instance == AssetInstances.ICONS.value
    assert icon_node.id == "weapons"
    assert icon_node.name == "inventory-pack-grid-icon-0"
    assert icon_node.bind.schema == Bindings.APERTURE.value
    assert isinstance(icon_node.bind.target, ApertureTarget)
    assert icon_node.bind.target.selector == "inventory-pack-grid"
    assert icon_node.bind.target.index == 0


def test_fabricator_expand_collection_uneven_capacity(
    mock_fabricator: Fabricator,
    mock_menu_context,
):
    node = MenuNode(
        id="weapons",
        name="uneven-grid",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(
            schema=Bindings.COLLECTION.value,
            target=CollectionTarget(
                source="context.inventory.pack",
                capacity=5,
                columns=4,
            ),
        ),
        parameters=GizmoParameters(
            capacity=5,
            columns=4,
            gap=5,
            pane="transparent",
            button="slot",
            dimensions=Scale(0.80, 0.40),
        ),
    )

    expanded = mock_fabricator.expand(node, context=mock_menu_context())
    params = expanded.parameters

    assert len(params.children) == 2
    row_0, row_1 = params.children
    assert len(row_0.parameters.children) == 4
    assert len(row_1.parameters.children) == 1

    last_slot = row_1.parameters.children[0]
    btn, icon = last_slot.parameters.children
    assert btn.name == "uneven-grid-slot-4"
    assert btn.bind.target.index == 4
    assert icon.name == "uneven-grid-icon-4"
    assert icon.bind.target.index == 4


def test_fabricator_expand_validation_errors(
    mock_fabricator: Fabricator,
    mock_collection_bind: MenuBinding,
    mock_menu_context,
):
    ctx = mock_menu_context()
    valid_params = GizmoParameters(
        capacity=8,
        columns=4,
        pane="transparent",
        button="slot",
    )

    node_no_bind = MenuNode(
        id="weapons",
        name="no-binding-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=None,
        parameters=valid_params,
    )
    with pytest.raises(ValueError, match="declared without a binding schema"):
        mock_fabricator.expand(node_no_bind, context=ctx)

    node_unknown_schema = MenuNode(
        id="weapons",
        name="unsupported-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(
            schema="unregistered_schema",
            target=mock_collection_bind.target,
        ),
        parameters=valid_params,
    )
    with pytest.raises(NotImplementedError, match="Unsupported gizmo schema"):
        mock_fabricator.expand(node_unknown_schema, context=ctx)

    node_wrong_params = MenuNode(
        id="weapons",
        name="wrong-params-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=mock_collection_bind,
        parameters=PaneParameters(),
    )
    with pytest.raises(TypeError, match="expects GizmoParameters"):
        mock_fabricator.expand(node_wrong_params, context=ctx)

    node_wrong_target = MenuNode(
        id="weapons",
        name="wrong-target-gizmo",
        instance=Shortcuts.GIZMOS.value,
        bind=MenuBinding(
            schema=Bindings.COLLECTION.value,
            target=SelectTarget(),
        ),
        parameters=valid_params,
    )
    with pytest.raises(TypeError, match="expects CollectionTarget"):
        mock_fabricator.expand(node_wrong_target, context=ctx)


@pytest.mark.parametrize(
    "capacity, columns, pane, button",
    [
        (0, 4, "transparent", "slot"),
        (8, 0, "transparent", "slot"),
        (8, 4, "", "slot"),
        (8, 4, "transparent", ""),
    ],
)
def test_gizmo_parameters_post_init_validation(
    capacity: int,
    columns: int,
    pane: str,
    button: str,
):
    with pytest.raises(ValueError):
        GizmoParameters(
            capacity=capacity,
            columns=columns,
            pane=pane,
            button=button,
        )