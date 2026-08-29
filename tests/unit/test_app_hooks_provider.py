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

@patch("app.hooks.provider.render")
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

@patch("app.hooks.provider.render")
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

@patch("app.hooks.provider.LayoutEngine")
def test_provider_unpack_menu(mock_layout_class, mock_provider):
    mock_layout = MagicMock()
    mock_btn_asset = MagicMock()
    mock_btn_asset.id = "test-btn"
    
    # Simulate flattening process output from layout engine
    mock_layout.compute.return_value = ([mock_btn_asset], {"test-btn": {}})
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
    assert "test-btn" in menu.widgets
    assert menu.widgets["test-btn"] == mock_btn_asset
    assert menu.focus == "test-btn"