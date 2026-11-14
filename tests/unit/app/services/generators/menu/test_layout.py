"""
@domain.test
@test.unit
@app.service
@app.module

# Ontology: Tests - tests.unit.app.services.generators.menus.test_layout

Unit tests for the Layout Module.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
from app.game.menus.bindings import SelectBinding
from app.services.generators.menus.layout import Layout
from app.models.config.menus import (
    MenuNode,
    PaneParameters,
    SelectTarget,
)
from app.models.core import AxisAlignment
from app.static.semantics import (
    Alignments,
    AssetCategories,
    AssetInstances,
    Layouts,
    Menus,
    Selections,
    Statuses,
    Traversal,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Scale,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_menu,
    pytest.mark.app_service,
]

# ---------------------------------------------------------------------------


def test_layout_quantize_9_slice_span(mock_asset):
    screensize = Dimensions(w=640, l=480)
    layout = Layout(screensize)

    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="dark-solid",
    )
    pane.taxonomy.name = "root-pane"

    wc = pane.properties.dimensions.w // 3  # 36 // 3 = 12
    lc = pane.properties.dimensions.l // 3  # 36 // 3 = 12

    pw, pl = 0.65, 0.50
    root_cfg = MenuNode(
        id="dark-solid",
        name="root-pane",
        instance=AssetInstances.PANES.value,
        parameters=PaneParameters(
            dimensions=Scale(pw, pl),
            children=[],
        ),
    )

    layout._quantize(root_cfg, {"root-pane": pane})

    w_req = int(pw * screensize.w)
    l_req = int(pl * screensize.l)
    expected_nx = max(0, math.ceil((w_req - 2 * wc) / wc))
    expected_ny = max(0, math.ceil((l_req - 2 * lc) / lc))

    assert pane.state.multiple.nx == expected_nx
    assert pane.state.multiple.ny == expected_ny
    assert pane.dimensions.w == (expected_nx + 2) * wc
    assert pane.dimensions.l == (expected_ny + 2) * lc


def test_layout_quantize_post_order_expands_parent_to_fit_children(mock_asset):
    """
    Verifies post-order quantization expands a parent dock pane's 9-slice span
    when the sum of its children's quantized spans and gaps exceeds its initial scale.
    """
    layout = Layout(Dimensions(w=480, l=480))

    parent = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="transparent",
    )
    parent.taxonomy.name = "parent-dock"
    parent.state.layout = Layouts.DOCK.value
    parent.state.gap = 5

    children_nodes = []
    widgets = {"parent-dock": parent}
    for i in range(4):
        slot_pane = mock_asset(
            AssetCategories.WIDGETS.value,
            AssetInstances.PANES.value,
            id="transparent",
        )
        slot_name = f"slot-{i}-pane"
        slot_pane.taxonomy.name = slot_name
        widgets[slot_name] = slot_pane
        children_nodes.append(
            MenuNode(
                id="transparent",
                name=slot_name,
                instance=AssetInstances.PANES.value,
                parameters=PaneParameters(dimensions=Scale(0.08, 0.08)),
            )
        )

    parent_cfg = MenuNode(
        id="transparent",
        name="parent-dock",
        instance=AssetInstances.PANES.value,
        parameters=PaneParameters(
            layout=Layouts.DOCK.value,
            gap=5,
            dimensions=Scale(0.32, 0.08),
            children=children_nodes,
        ),
    )

    layout._quantize(parent_cfg, widgets)

    # Each child quantizes to 48px; 4 * 48 + 3 * 5 = 207px -> next multiple of 12 is 216px
    assert all(widgets[f"slot-{i}-pane"].dimensions.w == 48 for i in range(4))
    assert parent.dimensions.w == 216
    assert parent.dimensions.l == 48


@pytest.mark.parametrize(
    "horiz, vert, margin, expected_x, expected_y",
    [
        (Alignments.START.value, Alignments.START.value, 10, 10, 10),
        (Alignments.CENTER.value, Alignments.CENTER.value, 10, (1000 - 108) // 2, (800 - 84) // 2),
        (Alignments.END.value, Alignments.END.value, 15, 1000 - 108 - 15, 800 - 84 - 15),
        (Alignments.CENTER.value, Alignments.END.value, 20, (1000 - 108) // 2, 800 - 84 - 20),
    ],
)
def test_layout_compute_root_justification(
    mock_asset,
    horiz: str,
    vert: str,
    margin: int,
    expected_x: int,
    expected_y: int,
):
    layout = Layout(Dimensions(w=1000, l=800))
    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="dark-solid",
    )
    pane.taxonomy.name = "p1"
    pane.state.justification = AxisAlignment(horizontal=horiz, vertical=vert)
    pane.state.margins = margin

    # Scale(0.1, 0.1) on 1000x800 with 36x36 pane (wc=12, lc=12) -> nx=7, ny=5 -> span=(108, 84)
    root_cfg = MenuNode(
        id="dark-solid",
        name="p1",
        instance=AssetInstances.PANES.value,
        parameters=PaneParameters(
            dimensions=Scale(0.1, 0.1),
            justification=AxisAlignment(horizontal=horiz, vertical=vert),
            margins=margin,
            children=[],
        ),
    )

    flattened, _ = layout.compute([root_cfg], {"p1": pane})

    assert flattened == [pane]
    assert pane.state.position.x == expected_x
    assert pane.state.position.y == expected_y


def test_layout_overlay_2_axis_alignment(mock_layout, mock_asset):
    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="transparent",
    )
    pane.state.margins = 10
    pane.state.position = Position(x=100, y=100)
    pane.state.span = Dimensions(w=200, l=200)

    child = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.BUTTONS.value,
        id="slot",
    )  # 40x40

    mock_layout._layout_overlay(
        pane,
        [child],
        AxisAlignment(horizontal=Alignments.CENTER.value, vertical=Alignments.CENTER.value),
    )
    assert child.state.position.x == 180
    assert child.state.position.y == 180

    mock_layout._layout_overlay(
        pane,
        [child],
        AxisAlignment(horizontal=Alignments.START.value, vertical=Alignments.END.value),
    )
    assert child.state.position.x == 110
    assert child.state.position.y == 250


def test_layout_dock_2_axis_alignment(mock_layout, mock_asset):
    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="transparent",
    )
    pane.state.margins = 5
    pane.state.position = Position(x=0, y=0)
    pane.state.span = Dimensions(w=120, l=100)

    c1 = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.BUTTONS.value,
        id="arrow-up",
    )  # 24x24
    c2 = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.BUTTONS.value,
        id="arrow-down",
    )  # 24x24

    # Total width = 24 + 24 + 12 = 60; centered X starts at (120 - 60) // 2 = 30
    mock_layout._layout_dock(
        pane,
        [c1, c2],
        AxisAlignment(horizontal=Alignments.CENTER.value, vertical=Alignments.CENTER.value),
        gap=12,
    )

    assert c1.state.position.x == 30
    assert c1.state.position.y == 38
    assert c2.state.position.x == 66
    assert c2.state.position.y == 38


def test_layout_stack_2_axis_alignment(mock_layout, mock_asset):
    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="transparent",
    )
    pane.state.margins = 10
    pane.state.position = Position(x=10, y=10)
    pane.state.span = Dimensions(w=120, l=120)

    c1 = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.BUTTONS.value,
        id="slot",
    )  # 40x40
    c2 = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.BUTTONS.value,
        id="slot",
    )  # 40x40

    # Total length = 40 + 40 + 10 = 90; centered Y starts at 10 + (120 - 90) // 2 = 25
    mock_layout._layout_stack(
        pane,
        [c1, c2],
        AxisAlignment(horizontal=Alignments.CENTER.value, vertical=Alignments.CENTER.value),
        gap=10,
    )

    assert c1.state.position.x == 50
    assert c1.state.position.y == 25
    assert c2.state.position.x == 50
    assert c2.state.position.y == 75


@pytest.mark.workflow_traversal
def test_layout_build_graph_cardinal_and_disabled_exclusion(mock_layout, mock_asset):
    def place_button(name: str, x: int, y: int, status: str = Statuses.IDLE.value):
        btn = mock_asset(
            AssetCategories.WIDGETS.value,
            AssetInstances.BUTTONS.value,
            id="slot",
        )
        btn.taxonomy.name = name
        btn.state.position = Position(x=x, y=y)
        btn.state.status = status
        return btn

    b_center = place_button("b_center", 100, 100)
    b_south = place_button("b_south", 100, 160)
    b_east = place_button("b_east", 160, 100)
    b_west = place_button("b_west", 40, 100)
    b_north = place_button("b_north", 100, 40)
    b_disabled = place_button("b_disabled", 100, 130, status=Statuses.DISABLED.value)

    graph = mock_layout._build_graph(
        [b_center, b_south, b_east, b_west, b_north, b_disabled]
    )

    assert "b_disabled" not in graph
    assert graph["b_center"][Traversal.SOUTH.value] == "b_south"
    assert graph["b_center"][Traversal.NORTH.value] == "b_north"
    assert graph["b_center"][Traversal.EAST.value] == "b_east"
    assert graph["b_center"][Traversal.WEST.value] == "b_west"
    assert graph["b_south"][Traversal.NORTH.value] == "b_center"
    assert graph["b_east"][Traversal.WEST.value] == "b_center"


@pytest.mark.menu_gizmo
@pytest.mark.workflow_traversal
def test_layout_build_graph_includes_disabled_gizmo_aperture_slots(
    mock_layout,
    mock_asset,
    mock_menu_context,
):
    """
    Verifies Bug B020 fix: Gizmo slot buttons (Selections.SLOT) are indexed into
    menu.graph even when initially DISABLED due to vacancy.
    """
    ctx = mock_menu_context()

    def place_gizmo_slot(index: int, x: int, status: str):
        btn = mock_asset(
            AssetCategories.WIDGETS.value,
            AssetInstances.BUTTONS.value,
            id="slot",
        )
        btn.taxonomy.name = f"weapons-grid-slot-{index}"
        btn.state.position = Position(x=x, y=100)
        btn.state.status = status
        btn.binding = SelectBinding(
            target=SelectTarget(
                selection=Selections.SLOT.value,
                selector="weapons-grid",
                index=index,
            ),
            context=ctx,
        )
        return btn

    s0 = place_gizmo_slot(0, 100, Statuses.IDLE.value)
    s1 = place_gizmo_slot(1, 150, Statuses.DISABLED.value)

    graph = mock_layout._build_graph([s0, s1])

    assert "weapons-grid-slot-0" in graph
    assert "weapons-grid-slot-1" in graph
    assert graph["weapons-grid-slot-0"][Traversal.EAST.value] == "weapons-grid-slot-1"
    assert graph["weapons-grid-slot-1"][Traversal.WEST.value] == "weapons-grid-slot-0"


@pytest.mark.workflow_traversal
def test_layout_full_menu_unpack_and_graph(mock_menu):
    main_menu = mock_menu(Menus.MAIN.value)

    assert main_menu.focus == "new-game"
    assert main_menu.graph["new-game"][Traversal.SOUTH.value] == "load-game"
    assert main_menu.graph["load-game"][Traversal.NORTH.value] == "new-game"
    assert main_menu.graph["load-game"][Traversal.SOUTH.value] == "options-menu"
    assert main_menu.graph["options-menu"][Traversal.SOUTH.value] == "editor-menu"