"""
# Ontology: tests.unit.test_app_services_generators_provider.py
"""
import pytest
from unittest.mock import MagicMock, patch

from app.models.config import MenuWidget, MenuPane, MenuConfiguration, MenuBinding
from app.config.enums import AssetInstances, Layouts, Alignments, Statuses
from libs.core.models import Dimensions, ScreenPosition
from app.game.menus.bindings.text import TextBinding, paginate

def test_provider_resolve():
    context = {
        "sprite": {
            "state": {
                "meters": {
                    "health": {"current": 50, "maximum": 100}
                }
            }
        }
    }
    
    binding = TextBinding(target={"content": "context.sprite.state.meters.health"}, context=context)
    assert binding.resolved["content"][0] == context["sprite"]["state"]["meters"]
    assert binding.resolved["content"][1] == "health"
    
    binding_invalid = TextBinding(target={"content": "context.sprite.state.invalid"}, context=context)
    assert binding_invalid.resolved["content"][0] == context["sprite"]["state"]
    assert binding_invalid.resolved["content"][1] == "invalid"


@patch("app.game.menus.bindings.text.render")
def test_provider_paginate(mock_render):
    def measure_side_effect(text, font):
        return (len(text) * 10, 10)
    
    mock_render.measure.side_effect = measure_side_effect
    mock_font = MagicMock()
    mock_font.margins = 0.0
    
    text = "one two three four five six"
    pages = paginate(text, mock_font, w=50, l=20)
    
    assert len(pages) == 3
    assert pages[0] == "one\ntwo"
    assert pages[1] == "three\nfour"
    assert pages[2] == "five\nsix"


@patch("app.game.menus.bindings.text.render")
@patch("app.services.generators.provider.render")
def test_provider_unpack_widget(mock_provider_render, mock_bindings_render, mock_provider):
    mock_provider_render.canvas.return_value = "mock_canvas_ptr"
    mock_bindings_render.measure.return_value = (10, 10)
    
    cfg = MenuWidget(
        instance=AssetInstances.PAGES.value,
        id="test-page",
        name="page-1",
        bind=MenuBinding(schema="text", target={"content": "context.text"}),
        status=Statuses.IDLE.value
    )
    context = {"text": "Hello World"}
    
    widget = mock_provider._unpack_widget(cfg, context)
    
    assert widget.id == "test-page"
    assert widget.name == "page-1"
    assert widget.state.content == ["Hello World"] 
    assert widget.state.canvas == "mock_canvas_ptr"


def test_provider_unpack_widget_traversal(mock_provider):
    cfg = MenuWidget(
        instance=AssetInstances.BUTTONS.value,
        id="test-btn",
        name="btn-1",
        bind=None,
        status=Statuses.DISABLED.value
    )
    widget = mock_provider._unpack_widget(cfg, {})
    assert widget.state.status == Statuses.DISABLED.value
    assert widget.state.animation.action == Statuses.DISABLED.value


def test_provider_unpack_widget_meter(mock_provider):
    cfg = MenuWidget(
        instance=AssetInstances.METERS.value,
        id="test-meter",
        name="meter-1",
        bind=MenuBinding(schema="meter", target={"meter": "context.hp"}),
        status=Statuses.IDLE.value
    )
    
    class MockHP:
        current = 75
        maximum = 100
    
    widget = mock_provider._unpack_widget(cfg, {"hp": MockHP()})
    assert widget.state.reading == 75
    assert widget.state.unit == 100
    assert widget.state.animation.frame == 75


@patch("app.services.generators.provider.Layout")
def test_provider_unpack_menu(mock_layout_class, mock_provider):
    # (Implementation remains mostly untouched, only the layout setup)
    mock_layout = MagicMock()
    mock_btn_asset = MagicMock()
    mock_btn_asset.id = "test-btn"
    mock_btn_asset.name = "btn-1" 
    
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
                        instance=AssetInstances.BUTTONS.value,
                        id="test-btn",
                        name="btn-1",
                        bind=None,
                        status=Statuses.IDLE.value
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


def test_provider_unpack_widget_icon(mock_provider):
    from app.models.config import MenuWidget, MenuBinding
    from app.config.enums import AssetInstances, Statuses
    
    cfg = MenuWidget(
        instance=AssetInstances.ICONS.value,
        id="test-icon",
        name="icon-1",
        bind=MenuBinding(schema="icon", target={"icon": "context.equipped_item"}),
        status=Statuses.IDLE.value
    )
    
    widget = mock_provider._unpack_widget(cfg, {"equipped_item": "sword_icon"})
    assert widget.state.icon == "sword_icon"
    assert widget.state.position.x == 0
    assert widget.state.position.y == 0