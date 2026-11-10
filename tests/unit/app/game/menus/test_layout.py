"""
@domain.test
@test.unit
@app.menu
@app.module

# Ontology: Tests - tests.unit.app.game.menus.test_layout

Unit tests for the Layout Module.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
from app.game.menus.modules import Layout
from app.models.config.menus import (
    MenuNode,
    PaneParameters,
)
from app.models.core import AxisAlignment
from app.static.semantics import (
    Alignments,
    AssetCategories,
    AssetInstances,
    Layouts,
    Menus,
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
    pytest.mark.app_module,
]

# ---------------------------------------------------------------------------


def test_layout_quantize_9_slice_span(mock_asset):
    screensize = Dimensions(w=640, l=480)
    layout = Layout(screensize)

    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="neutral",
    )
    pane.taxonomy.name = "root-pane"

    wc = pane.properties.dimensions.w // 3  # 318 // 3 = 106
    lc = pane.properties.dimensions.l // 3  # 180 // 3 = 60

    pw, pl = 0.65, 0.50
    root_cfg = MenuNode(
        id="neutral",
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


@pytest.mark.parametrize(
    "horiz, vert, margin, expected_x, expected_y",
    [
        (Alignments.START.value, Alignments.START.value, 10, 10, 10),
        (Alignments.CENTER.value, Alignments.CENTER.value, 10, (1000 - 212) // 2, (800 - 120) // 2),
        (Alignments.END.value, Alignments.END.value, 15, 1000 - 212 - 15, 800 - 120 - 15),
        (Alignments.CENTER.value, Alignments.END.value, 20, (1000 - 212) // 2, 800 - 120 - 20),
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
        id="dark",
    )
    pane.taxonomy.name = "p1"
    pane.state.justification = AxisAlignment(horizontal=horiz, vertical=vert)
    pane.state.margins = margin

    # Small scale clamps nx=0, ny=0 -> span = (2 * 106, 2 * 60) = (212, 120)
    root_cfg = MenuNode(
        id="dark",
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


@pytest.mark.workflow_traversal
def test_layout_full_menu_unpack_and_graph(mock_menu):
    main_menu = mock_menu(Menus.MAIN.value)

    assert main_menu.focus == "new-game"
    assert main_menu.graph["new-game"][Traversal.SOUTH.value] == "load-game"
    assert main_menu.graph["load-game"][Traversal.NORTH.value] == "new-game"
    assert main_menu.graph["load-game"][Traversal.SOUTH.value] == "options-menu"
    assert main_menu.graph["options-menu"][Traversal.SOUTH.value] == "editor-menu"