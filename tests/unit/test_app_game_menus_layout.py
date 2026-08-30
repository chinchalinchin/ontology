"""
# Ontology: tests.unit.test_app_game_menus_layout
"""
import pytest
from unittest.mock import MagicMock

from app.game.menus.layout import Layout
from app.models.config import MenuPane, MenuWidget
from app.config.enums import Layouts, Alignments, Traversal
from libs.core.models import Dimensions, Position, ScreenPosition
from app.models.state import PaneState, TraversalState

def test_layout_compute_anchor():
    layout = Layout(Dimensions(w=1000, l=1000))
    root_cfg = MenuPane(
        id="p1", name="p1", 
        position=ScreenPosition(px=0.5, py=0.25), 
        layout=Layouts.OVERLAY, alignment=Alignments.CENTER, 
        gap=0, children=[]
    )
    mock_pane = MagicMock()
    mock_pane.state = PaneState(position=Position(x=0,y=0), layout=Layouts.OVERLAY, alignment=Alignments.CENTER, gap=0)
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

    # Usable space: 180x180. Center offset: (180 - 50)//2 = 65.
    # Absolute coordinate: 100 (pane_pos) + 10 (margin) + 65 (offset) = 175.
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
    
    # Total w = 50. Offset x = (100 - 50) // 2 = 25
    # Y offset = (100 - 20) // 2 = 40
    assert c1.state.position.x == 25
    assert c1.state.position.y == 40
    assert c2.state.position.x == 55  # 25 + 20 + gap(10)
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
    
    # Inner usable space = 100x100
    # Total l = 20 + 10 + 20 = 50. Offset y = (100 - 50) // 2 = 25
    # X offset = (100 - 40) // 2 = 30
    # Absolute X: 10 + 10 + 30 = 50
    # Absolute Y c1: 10 + 10 + 25 = 45
    assert c1.state.position.x == 50
    assert c1.state.position.y == 45
    assert c2.state.position.x == 50
    assert c2.state.position.y == 75

def test_layout_build_graph():
    layout = Layout(Dimensions(w=1000, l=1000))
    
    def mock_button(name, x, y, w, l):
        b = MagicMock()
        b.name = name
        b.instance = 'buttons'
        b.state.position = Position(x=x, y=y)
        b.dimensions = Dimensions(w=w, l=l)
        return b
        
    b1 = mock_button("b1", 100, 100, 50, 50)
    b2 = mock_button("b2", 100, 160, 50, 50) # South of b1
    b3 = mock_button("b3", 160, 100, 50, 50) # East of b1
    b4 = mock_button("b4", 40, 100, 50, 50)  # West of b1
    b5 = mock_button("b5", 100, 40, 50, 50)  # North of b1

    graph = layout._build_graph([b1, b2, b3, b4, b5])
    
    assert graph["b1"][Traversal.SOUTH] == "b2"
    assert graph["b1"][Traversal.EAST] == "b3"
    assert graph["b1"][Traversal.WEST] == "b4"
    assert graph["b1"][Traversal.NORTH] == "b5"
    
    # Reverse validation bounds check
    assert graph["b2"][Traversal.NORTH] == "b1"
    assert graph["b3"][Traversal.WEST] == "b1"