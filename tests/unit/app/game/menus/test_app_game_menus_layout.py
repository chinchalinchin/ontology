"""
# Ontology: tests.unit.test_app_game_menus_layout
"""
from unittest.mock import MagicMock
import pytest

from app.game.menus.layout import Layout
from app.models.config.menus import MenuNode, PaneParameters, ButtonParameters
from app.config.enums import Layouts, Alignments, Traversal, Statuses, AssetInstances
from libs.core.models import Dimensions, Position, ScreenPosition
from app.models.state import PaneState, TraversalState
from app.assets.base import Asset, Taxonomy
from app.models.properties import WidgetProperties


def test_layout_compute_anchor():
    layout = Layout(Dimensions(w=1000, l=1000))
    root_cfg = MenuNode(
        id="p1", 
        name="p1",
        instance=AssetInstances.PANES.value,
        parameters=PaneParameters(
            position=ScreenPosition(px=0.5, py=0.25), 
            layout=Layouts.OVERLAY, 
            alignment=Alignments.CENTER, 
            gap=0, 
            children=[]
        )
    )
    mock_pane = MagicMock()
    mock_pane.state = PaneState(position=Position(x=0, y=0), layout=Layouts.OVERLAY, alignment=Alignments.CENTER, gap=0)
    widgets = {"p1": mock_pane}
    
    layout.compute([root_cfg], widgets)
    
    assert mock_pane.state.position.x == 500
    assert mock_pane.state.position.y == 250


def test_layout_overlay():
    layout = Layout(Dimensions(w=1000, l=1000))
    pane = MagicMock()
    pane.state.margins = 10
    pane.state.position = Position(x=100, y=100)
    pane.dimensions = Dimensions(w=200, l=200)

    child = MagicMock()
    child.dimensions = Dimensions(w=50, l=50)

    layout._layout_overlay(pane, [child])

    assert child.state.position.x == 175
    assert child.state.position.y == 175


def test_layout_dock_center():
    layout = Layout(Dimensions(w=1000, l=1000))
    pane = MagicMock()
    pane.state.margins = 0
    pane.state.position = Position(x=0, y=0)
    pane.dimensions = Dimensions(w=100, l=100)

    c1 = MagicMock()
    c1.dimensions = Dimensions(w=20, l=20)
    c2 = MagicMock()
    c2.dimensions = Dimensions(w=20, l=20)

    layout._layout_dock(pane, [c1, c2], Alignments.CENTER, gap=10)
    
    assert c1.state.position.x == 25
    assert c1.state.position.y == 40
    assert c2.state.position.x == 55
    assert c2.state.position.y == 40


def test_layout_stack_center():
    layout = Layout(Dimensions(w=1000, l=1000))
    pane = MagicMock()
    pane.state.margins = 10
    pane.state.position = Position(x=10, y=10)
    pane.dimensions = Dimensions(w=120, l=120)

    c1 = MagicMock()
    c1.dimensions = Dimensions(w=40, l=20)
    c2 = MagicMock()
    c2.dimensions = Dimensions(w=40, l=20)

    layout._layout_stack(pane, [c1, c2], Alignments.CENTER, gap=10)
    
    assert c1.state.position.x == 50
    assert c1.state.position.y == 45
    assert c2.state.position.x == 50
    assert c2.state.position.y == 75


def test_layout_dock_with_explicit_dimensions():
    """Validates that adjacent dock containers respect explicit geometry without overlapping."""
    layout = Layout(Dimensions(w=640, l=480))
    root_pane = Asset(
        taxonomy=Taxonomy("neutral", "root", "widgets", AssetInstances.PANES.value),
        properties=WidgetProperties(dimensions=Dimensions(w=318, l=180)),
        state=PaneState(position=Position(x=0, y=0), margins=10, gap=10)
    )

    grid_pane = Asset(
        taxonomy=Taxonomy("transparent-slot", "grid", "widgets", AssetInstances.PANES.value),
        properties=WidgetProperties(dimensions=Dimensions(w=175, l=85)),
        state=PaneState(margins=0)
    )
    scroll_pane = Asset(
        taxonomy=Taxonomy("transparent-slot", "controls", "widgets", AssetInstances.PANES.value),
        properties=WidgetProperties(dimensions=Dimensions(w=24, l=85)),
        state=PaneState(margins=0)
    )

    layout._layout_dock(root_pane, [grid_pane, scroll_pane], Alignments.CENTER, gap=10)

    assert grid_pane.state.position.x + grid_pane.dimensions.w <= scroll_pane.state.position.x
    assert scroll_pane.state.position.x - (grid_pane.state.position.x + grid_pane.dimensions.w) == 10


def test_layout_build_graph():
    layout = Layout(Dimensions(w=1000, l=1000))
    
    def mock_button(name, x, y, w, l):
        b = MagicMock()
        b.name = name
        b.instance = AssetInstances.BUTTONS.value
        b.state.position = Position(x=x, y=y)
        b.state.status = Statuses.IDLE.value
        b.dimensions = Dimensions(w=w, l=l)
        return b
        
    b1 = mock_button("b1", 100, 100, 50, 50)
    b2 = mock_button("b2", 100, 160, 50, 50)
    b3 = mock_button("b3", 160, 100, 50, 50)
    b4 = mock_button("b4", 40, 100, 50, 50)
    b5 = mock_button("b5", 100, 40, 50, 50)

    graph = layout._build_graph([b1, b2, b3, b4, b5])
    
    assert graph["b1"][Traversal.SOUTH] == "b2"
    assert graph["b1"][Traversal.EAST] == "b3"
    assert graph["b1"][Traversal.WEST] == "b4"
    assert graph["b1"][Traversal.NORTH] == "b5"
    assert graph["b2"][Traversal.NORTH] == "b1"
    assert graph["b3"][Traversal.WEST] == "b1"


def test_layout_build_graph_grid_to_controls():
    """Validates that right-column buttons in a 2x2 grid link EAST to adjacent scroll controls."""
    layout = Layout(Dimensions(w=640, l=480))

    def make_btn(name, x, y, w=40, l=40):
        b = MagicMock()
        b.name = name
        b.instance = AssetInstances.BUTTONS.value
        b.state.position = Position(x=x, y=y)
        b.state.status = Statuses.IDLE.value
        b.dimensions = Dimensions(w=w, l=l)
        return b

    slot_0 = make_btn("slot-0", 100, 100)
    slot_1 = make_btn("slot-1", 145, 100)
    slot_2 = make_btn("slot-2", 100, 145)
    slot_3 = make_btn("slot-3", 145, 145)

    arrow_up = make_btn("arrow-up", 200, 100, w=24, l=24)
    arrow_down = make_btn("arrow-down", 200, 145, w=24, l=24)

    buttons = [slot_0, slot_1, slot_2, slot_3, arrow_up, arrow_down]
    graph = layout._build_graph(buttons)

    assert graph["slot-1"][Traversal.EAST] == "arrow-up"
    assert graph["slot-3"][Traversal.EAST] == "arrow-down"
    assert graph["arrow-up"][Traversal.WEST] == "slot-1"
    assert graph["arrow-down"][Traversal.WEST] == "slot-3"