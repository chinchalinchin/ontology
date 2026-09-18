"""
# Ontology: tests.unit.test_app_services_generators_menus_provider
"""
# Standard Libraries
from unittest.mock import MagicMock, patch

# Application Libraries
from app.models.config.menus import (
    MenuNode, 
    PaneParameters, 
    ButtonParameters, 
    MenuConfiguration, 
    MenuBinding
)
from app.config.enums import (
    AssetInstances, 
    Layouts, 
    Alignments, 
    Statuses, 
    Fonts, 
    Bindings, 
)
from app.game.menus.bindings.text import TextBinding, paginate
from app.models.state.widgets import CollectionState

# Cython Libraries
from libs.core.models import Dimensions, ScreenPosition


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
    mock_render.measure.side_effect = lambda text, font: (len(text) * 10, 10)
    mock_font = MagicMock()
    mock_font.margins = 0.0
    
    text = "one two three four five six"
    pages = paginate(text, mock_font, w=50, l=20)
    
    assert len(pages) == 3
    assert pages[0] == "one\ntwo"
    assert pages[1] == "three\nfour"
    assert pages[2] == "five\nsix"


@patch("app.game.menus.bindings.text.render")
@patch("app.services.generators.menus.provider.render")
def test_provider_unpack_widget_page(mock_provider_render, mock_bindings_render, mock_provider):
    mock_provider_render.canvas.return_value = "mock_canvas_ptr"
    mock_bindings_render.measure.return_value = (10, 10)
    
    cfg = MenuNode(
        id="test-page",
        name="page-1",
        instance=AssetInstances.PAGES.value,
        bind=MenuBinding(schema=Bindings.TEXT.value, target={"content": "context.text"})
    )
    context = {"text": "Hello World"}
    
    widget = mock_provider._unpack_widget(cfg, context, Fonts.DIALOGUE.value, {})
    
    assert widget.id == "test-page"
    assert widget.name == "page-1"
    assert widget.state.content == ["Hello World"] 
    assert widget.state.canvas == "mock_canvas_ptr"


def test_provider_unpack_widget_traversal(mock_provider):
    cfg = MenuNode(
        id="test-btn",
        name="btn-1",
        instance=AssetInstances.BUTTONS.value,
        parameters=ButtonParameters(status=Statuses.DISABLED.value)
    )
    widget = mock_provider._unpack_widget(cfg, {}, Fonts.MENU.value, {})
    assert widget.state.status == Statuses.DISABLED.value
    assert widget.state.animation.action == Statuses.DISABLED.value


def test_provider_unpack_widget_meter(mock_provider):
    cfg = MenuNode(
        id="test-meter",
        name="meter-1",
        instance=AssetInstances.METERS.value,
        bind=MenuBinding(schema=Bindings.METER.value, target={"meter": "context.hp"})
    )
    
    class MockHP:
        current = 75
        maximum = 100
    
    widget = mock_provider._unpack_widget(cfg, {"hp": MockHP()}, Fonts.MENU.value, {})
    assert widget.state.reading == 75
    assert widget.state.unit == 100
    assert widget.state.animation.frame == 75


def test_provider_unpack_widget_icon(mock_provider):
    cfg = MenuNode(
        id="test-icon",
        name="icon-1",
        instance=AssetInstances.ICONS.value,
        bind=MenuBinding(
            schema=Bindings.ICON.value, 
            target={"icon": "context.equipped_item"}
        )
    )
    
    widget = mock_provider._unpack_widget(cfg, {"equipped_item": "sword"}, Fonts.MENU.value, {})
    assert widget.state.icon == "sword"
    assert widget.state.position.x == 0
    assert widget.state.position.y == 0


def test_provider_expand_tree_gizmo(mock_provider, mock_gizmo_node):
    context = {"inventory": {"pack": ["shortsword"]}}
    expanded = mock_provider._expand_tree(mock_gizmo_node, context)

    assert expanded.instance == AssetInstances.PANES.value
    assert isinstance(expanded.parameters, PaneParameters)
    assert expanded.bind.schema == Bindings.COLLECTION.value
    assert len(expanded.parameters.children) == 2  # 8 slots over 4 columns = 2 row panes


def test_provider_unpack_pane_collection_state(mock_provider):
    pane_node = MenuNode(
        id="transparent-slot",
        name="inventory-pack-grid",
        instance=AssetInstances.PANES.value,
        bind=MenuBinding(
            schema=Bindings.COLLECTION.value,
            target={"source": "context.inventory.pack", "capacity": "8", "columns": "4"}
        ),
        parameters=PaneParameters(
            layout=Layouts.STACK,
            alignment=Alignments.START,
            dimensions=Dimensions(w=175, l=85)
        )
    )
    context = {"inventory": {"pack": ["shortsword", "dagger"]}}
    widgets = {}

    mock_provider._unpack_pane(pane_node, context, widgets)

    grid_asset = widgets["inventory-pack-grid"]
    assert isinstance(grid_asset.state, CollectionState)
    assert grid_asset.state.capacity == 8
    assert grid_asset.state.columns == 4
    assert grid_asset.state.get_item(0) == "shortsword"
    assert grid_asset.state.get_item(1) == "dagger"
    assert grid_asset.state.get_item(2) == ""
    assert grid_asset.properties.dimensions.w == 175
    assert grid_asset.properties.dimensions.l == 85


@patch("app.services.generators.menus.provider.Layout")
def test_provider_unpack_menu(mock_layout_class, mock_provider):
    mock_layout = MagicMock()
    mock_btn_asset = MagicMock()
    mock_btn_asset.id = "test-btn"
    mock_btn_asset.name = "btn-1"
    mock_btn_asset.instance = AssetInstances.BUTTONS.value
    mock_btn_asset.state.status = Statuses.IDLE.value
    
    mock_layout.compute.return_value = ([mock_btn_asset], {"btn-1": {}})
    mock_layout_class.return_value = mock_layout
    
    cfg = MenuConfiguration(
        controller="scroll",
        roots=[
            MenuNode(
                id="test-pane",
                name="pane-1",
                instance=AssetInstances.PANES.value,
                parameters=PaneParameters(
                    position=ScreenPosition(px=0.0, py=0.0),
                    layout=Layouts.DOCK,
                    alignment=Alignments.START,
                    gap=5,
                    children=[
                        MenuNode(
                            id="test-btn",
                            name="btn-1",
                            instance=AssetInstances.BUTTONS.value,
                            parameters=ButtonParameters(status=Statuses.IDLE)
                        )
                    ]
                )
            )
        ]
    )
    
    menu = mock_provider.unpack("menu-id", cfg, {}, Dimensions(w=800, l=600))
    
    assert menu.id == "menu-id"
    assert menu.controller is not None
    assert "btn-1" in menu.widgets
    assert menu.widgets["btn-1"] == mock_btn_asset
    assert menu.focus == "btn-1"