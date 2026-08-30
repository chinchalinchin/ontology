"""
# Ontology: tests.unit.test_app_hooks_provider.py
"""
import pytest
from unittest.mock import MagicMock, patch

from app.models.config import MenuWidget, MenuPane, MenuConfiguration
from app.game.menus.core import Binding
from app.config.enums import AssetInstances, Layouts, Alignments, Statuses
from libs.core.models import Dimensions, ScreenPosition


def test_provider_resolve(mock_provider):
    context = {
        "sprite": {
            "state": {
                "meters": {
                    "health": {"current": 50, "maximum": 100}
                }
            }
        }
    }
    
    res = mock_provider._resolve("context.sprite.state.meters.health", context)
    assert res == {"current": 50, "maximum": 100}
    
    res_invalid = mock_provider._resolve("context.sprite.state.invalid", context)
    assert res_invalid is None

@patch("app.services.generators.provider.render")
def test_provider_paginate(mock_render, mock_provider):
    def measure_side_effect(text, font):
        return (len(text) * 10, 10)
    
    mock_render.measure.side_effect = measure_side_effect
    mock_font = MagicMock()
    mock_font.margins = 0.0
    
    text = "one two three four five six"
    pages = mock_provider._paginate(text, mock_font, w=50, l=20)
    
    assert len(pages) == 3
    assert pages[0] == "one\ntwo"
    assert pages[1] == "three\nfour"
    assert pages[2] == "five\nsix"

@patch("app.services.generators.provider.render")
def test_provider_unpack_widget(mock_render, mock_provider):
    mock_render.canvas.return_value = "mock_canvas_ptr"
    mock_render.measure.return_value = (10, 10)
    
    cfg = MenuWidget(
        instance=AssetInstances.PAGES,
        id="test-page",
        name="page-1",
        bind=Binding(state="context.text"),
        status=Statuses.IDLE
    )
    context = {"text": "Hello World"}
    
    widget = mock_provider._unpack_widget(cfg, context)
    
    assert widget.id == "test-page"
    assert widget.name == "page-1"
    assert widget.state.content == ["Hello World"] 
    assert widget.state.canvas == "mock_canvas_ptr"
    assert widget.state.text is True

def test_provider_unpack_widget_traversal(mock_provider):
    """Verify Traversal widget unpacks with synced starting action."""
    cfg = MenuWidget(
        instance=AssetInstances.BUTTONS,
        id="test-btn",
        name="btn-1",
        bind=Binding(),
        status=Statuses.DISABLED
    )
    widget = mock_provider._unpack_widget(cfg, {})
    assert widget.state.status == Statuses.DISABLED.value
    assert widget.state.animation.action == Statuses.DISABLED.value

def test_provider_unpack_widget_meter(mock_provider):
    """Verify Meter widget calculates its initial frame instantly to prevent 1-frame flicker."""
    cfg = MenuWidget(
        instance=AssetInstances.METERS,
        id="test-meter",
        name="meter-1",
        bind=Binding(state="context.hp"),
        status=Statuses.IDLE
    )
    
    class MockHP:
        current = 75
        maximum = 100
    
    widget = mock_provider._unpack_widget(cfg, {"hp": MockHP()})
    assert widget.state.reading == 75
    assert widget.state.unit == 100
    assert widget.state.animation.frame == 75

@patch("app.services.generators.provider.LayoutEngine")
def test_provider_unpack_menu(mock_layout_class, mock_provider):
    mock_layout = MagicMock()
    mock_btn_asset = MagicMock()
    mock_btn_asset.id = "test-btn"
    mock_btn_asset.name = "btn-1" # Fix: Assign name so unpacking loop registers properly
    
    # Simulate flattening process output from layout engine
    mock_layout.compute.return_value = ([mock_btn_asset], {"btn-1": {}})
    mock_layout_class.return_value = mock_layout
    
    cfg = MenuConfiguration(
        controller="scroll",
        roots=[
            MenuPane(
                id="test-pane",
                name="pane-1",
                position=ScreenPosition(px=0.0, py=0.0),
                layout=Layouts.DOCK,
                alignment=Alignments.START,
                gap=5,
                children=[
                    MenuWidget(
                        instance=AssetInstances.BUTTONS,
                        id="test-btn",
                        name="btn-1",
                        bind=Binding(),
                        status=Statuses.IDLE
                    )
                ]
            )
        ]
    )
    
    menu = mock_provider.unpack("menu-id", cfg, {}, Dimensions(w=800, l=600))
    
    assert menu.id == "menu-id"
    assert menu.controller is not None
    assert "btn-1" in menu.widgets
    assert menu.widgets["btn-1"] == mock_btn_asset
    assert menu.focus == "btn-1"