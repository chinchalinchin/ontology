"""
@domain.test
@test.unit
@app.service
@app.menu
@category.widgets

# Ontology: Tests - tests.unit.app.services.generators.menu.test_provider

Unit tests for the Provider service.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.menus.bindings.text import (
    TextBinding,
    paginate,
)
from app.models.config.menus import (
    ButtonParameters,
    CollectionTarget,
    IconTarget,
    MenuBinding,
    MenuConfiguration,
    MenuNode,
    MeterTarget,
    PaneParameters,
    TextTarget,
)
from app.models.core import AxisAlignment
from app.models.state.assets.widgets import (
    CollectionState,
    PaneState,
)
from app.static.semantics import (
    Alignments,
    AssetInstances,
    Bindings,
    Controllers,
    Fonts,
    Layouts,
    Menus,
    Statuses,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Scale,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
    pytest.mark.app_menu,
    pytest.mark.category_widgets,
]

# ---------------------------------------------------------------------------


def test_provider_text_binding_resolve(mock_menu_context):
    ctx = mock_menu_context(Menus.VIEW.value)
    binding = TextBinding(
        target=TextTarget(content="context.sprite.meters.health.current"),
        context=ctx,
    )
    parent, attr = binding._content_ref
    assert parent == ctx.sprite.meters.health
    assert attr == "current"


@pytest.mark.workflow_typography
def test_provider_paginate(mock_render, mock_registry):
    mock_render.measure.side_effect = lambda text, font: (len(text) * 10, 10)
    font = mock_registry.font(Fonts.DIALOGUE.value)
    font.margins = 0.0

    text = "one two three four five six"
    pages = paginate(text, font, w=50, l=20)

    assert len(pages) == 3
    assert pages[0] == "one\ntwo"
    assert pages[1] == "three\nfour"
    assert pages[2] == "five\nsix"


@pytest.mark.workflow_typography
@pytest.mark.workflow_rendering
def test_provider_unpack_and_bake_text_pane(
    mock_provider,
    mock_render,
    mock_menu_context,
    mock_screen,
):
    ctx = mock_menu_context(Menus.TEXT.value)
    cfg = MenuConfiguration(
        controller=Controllers.SCROLL.value,
        roots=[
            MenuNode(
                id="dark",
                name="page-pane",
                instance=AssetInstances.PANES.value,
                parameters=PaneParameters(
                    dimensions=Scale(0.50, 0.25),
                    font=Fonts.DIALOGUE.value,
                ),
                bind=MenuBinding(
                    schema=Bindings.TEXT.value,
                    target=TextTarget(content="context.content"),
                ),
            )
        ],
    )

    menu = mock_provider.unpack("text", cfg, ctx, mock_screen.screensize)
    pane = menu.widgets["page-pane"]

    assert isinstance(pane.state, PaneState)
    assert pane.state.canvas is not None
    assert pane.state.current() != ""
    mock_render.construct.assert_called()
    mock_render.write.assert_called()


def test_provider_unpack_widget_traversal(mock_provider, mock_menu_context):
    cfg = MenuNode(
        id="label",
        name="btn-1",
        instance=AssetInstances.BUTTONS.value,
        parameters=ButtonParameters(status=Statuses.DISABLED.value),
    )
    widget = mock_provider._widget(cfg, mock_menu_context(), {})
    assert widget.state.status == Statuses.DISABLED.value


def test_provider_unpack_widget_meter(mock_provider, mock_menu_context):
    ctx = mock_menu_context(Menus.VIEW.value)
    cfg = MenuNode(
        id="health",
        name="meter-1",
        instance=AssetInstances.METERS.value,
        bind=MenuBinding(
            schema=Bindings.METER.value,
            target=MeterTarget(meter="context.sprite.meters.health"),
        ),
    )

    widget = mock_provider._widget(cfg, ctx, {})
    assert widget.state.reading == ctx.sprite.meters.health.current
    assert widget.state.unit == ctx.sprite.meters.health.maximum


def test_provider_unpack_widget_icon(mock_provider, mock_menu_context):
    ctx = mock_menu_context(Menus.VIEW.value)
    cfg = MenuNode(
        id="weapons",
        name="icon-1",
        instance=AssetInstances.ICONS.value,
        bind=MenuBinding(
            schema=Bindings.ICON.value,
            target=IconTarget(icon="context.sprite.inventory.equipment.weapon"),
        ),
    )

    widget = mock_provider._widget(cfg, ctx, {})
    assert widget.state.icon == ctx.sprite.inventory.equipment.weapon
    assert widget.state.position.x == 0
    assert widget.state.position.y == 0


@pytest.mark.menu_gizmo
def test_provider_expand_and_unpack_gizmo_collection_state(
    mock_provider,
    mock_gizmo_node,
):
    context = {"inventory": {"pack": ["shortsword", "dagger"]}}
    expanded = mock_provider._expand(mock_gizmo_node, context)

    assert expanded.instance == AssetInstances.PANES.value
    assert isinstance(expanded.parameters, PaneParameters)
    assert expanded.bind.schema == Bindings.COLLECTION.value
    assert len(expanded.parameters.children) == 2

    widgets = {}
    mock_provider._unpack_pane(expanded, context, widgets)

    grid_asset = widgets["inventory-pack-grid"]
    assert isinstance(grid_asset.state, CollectionState)
    assert grid_asset.state.capacity == 8
    assert grid_asset.state.columns == 4
    assert grid_asset.state.get_item(0) == "shortsword"
    assert grid_asset.state.get_item(1) == "dagger"
    assert grid_asset.state.get_item(2) == ""

    # Occupied slots are IDLE, vacant slots are synchronized to DISABLED
    assert widgets["inventory-pack-grid-slot-0"].state.status == Statuses.IDLE.value
    assert widgets["inventory-pack-grid-slot-1"].state.status == Statuses.IDLE.value
    assert widgets["inventory-pack-grid-slot-2"].state.status == Statuses.DISABLED.value


@pytest.mark.workflow_typography
def test_provider_lexical_font_inheritance(mock_provider, mock_menu_context):
    root_node = MenuNode(
        id="neutral",
        name="root-pane",
        instance=AssetInstances.PANES.value,
        parameters=PaneParameters(
            font=Fonts.MENU.value,
            children=[
                MenuNode(
                    id="transparent",
                    name="inherited-child-pane",
                    instance=AssetInstances.PANES.value,
                    parameters=PaneParameters(font=None),
                ),
                MenuNode(
                    id="transparent",
                    name="overridden-child-pane",
                    instance=AssetInstances.PANES.value,
                    parameters=PaneParameters(font=Fonts.TITLE.value),
                ),
            ],
        ),
    )

    widgets = {}
    mock_provider._unpack_pane(root_node, mock_menu_context(), widgets)

    assert widgets["root-pane"].state.font == Fonts.MENU.value
    assert widgets["inherited-child-pane"].state.font == Fonts.MENU.value
    assert widgets["overridden-child-pane"].state.font == Fonts.TITLE.value


def test_provider_unpack_view_overlay_has_no_focus(mock_menu):
    hud = mock_menu(Menus.VIEW.value)
    assert hud.id == Menus.VIEW.value
    assert hud.focus is None
    assert "health-meter" in hud.widgets
    assert "magic-meter" in hud.widgets