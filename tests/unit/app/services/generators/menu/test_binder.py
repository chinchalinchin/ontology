"""
@domain.test
@test.unit
@app.service
@app.menu
@menu.binding
@menu.gizmo

# Ontology: Tests - tests.unit.app.services.generators.menu.test_binder

Unit tests for the Binder service and Binding closures.
"""
# External Libraries
import pytest

# Application Libraries
from app.game.menus.bindings import (
    ApertureBinding,
    CollectionBinding,
    IconBinding,
    LibraryBinding,
    MeterBinding,
    SelectBinding,
    TextBinding,
)
from app.models.config.menus import (
    CollectionTarget,
    MenuBinding,
    TextTarget,
)
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Bindings,
    Menus,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_service,
    pytest.mark.app_menu,
    pytest.mark.menu_binding,
]

# ---------------------------------------------------------------------------


@pytest.mark.workflow_plots
def test_binding_library(mock_binder, mock_library_bind, mock_menu_context):
    ctx = mock_menu_context(Menus.DIALOGUE.value)
    binding = mock_binder.binding(mock_library_bind, ctx)

    assert isinstance(binding, LibraryBinding)
    assert binding.registry == mock_binder.registry
    assert binding.library == mock_binder.library


def test_binding_meter(mock_binder, mock_meter_bind, mock_menu_context):
    ctx = mock_menu_context(Menus.VIEW.value)
    binding = mock_binder.binding(mock_meter_bind, ctx)

    assert isinstance(binding, MeterBinding)
    reading_fn, unit_fn = binding.bind()
    assert reading_fn() == ctx.sprite.meters.health.current
    assert unit_fn() == ctx.sprite.meters.health.maximum


def test_binding_icon(mock_binder, mock_icon_bind, mock_menu_context):
    ctx = mock_menu_context(Menus.VIEW.value)
    binding = mock_binder.binding(mock_icon_bind, ctx)

    assert isinstance(binding, IconBinding)
    icon_fn = binding.bind()
    assert icon_fn() == ctx.sprite.slots.equipment.weapon


def test_binding_select(mock_binder, mock_select_bind, mock_menu_context):
    ctx = mock_menu_context(Menus.DIALOGUE.value)
    binding = mock_binder.binding(mock_select_bind, ctx)

    assert isinstance(binding, SelectBinding)
    assert binding.selection == mock_select_bind.target.selection
    assert binding.selector == mock_select_bind.target.selector


@pytest.mark.menu_gizmo
def test_binding_collection_list_and_dict(
    mock_binder,
    mock_collection_bind,
    mock_menu_context,
):
    ctx = mock_menu_context(Menus.INVENTORY.value)
    binding = mock_binder.binding(mock_collection_bind, ctx)
    assert isinstance(binding, CollectionBinding)
    assert isinstance(binding.bind()(), list)

    dict_ctx = {"inventory": {"pack": {"sword": 1, "dagger": 0, "buckler": 2}}}
    dict_binding = mock_binder.binding(
        MenuBinding(
            schema=Bindings.COLLECTION.value,
            target=CollectionTarget(source="context.inventory.pack"),
        ),
        dict_ctx,
    )
    assert dict_binding.get_collection() == ["sword", "buckler"]


@pytest.mark.menu_gizmo
def test_binding_aperture_occupied_and_vacant(
    mock_binder,
    mock_asset,
    mock_collection_state,
    mock_aperture_bind,
    mock_aperture_bind_alt,
    mock_menu_context,
):
    pane = mock_asset(
        AssetCategories.WIDGETS.value,
        AssetInstances.PANES.value,
        id="transparent",
        asset_state=mock_collection_state,
    )
    widgets = {"inventory-pack-grid": pane}
    ctx = mock_menu_context(Menus.INVENTORY.value)

    occupied_binding = mock_binder.binding(mock_aperture_bind, ctx, widgets=widgets)
    assert isinstance(occupied_binding, ApertureBinding)
    assert occupied_binding.get_item() == "sword"

    vacant_binding = mock_binder.binding(mock_aperture_bind_alt, ctx, widgets=widgets)
    assert vacant_binding.get_item() == ""

    missing_pane_binding = mock_binder.binding(mock_aperture_bind, ctx, widgets={})
    assert missing_pane_binding.get_item() == ""


def test_binding_fallback_text_and_none(mock_binder, mock_menu_context):
    ctx = mock_menu_context(Menus.TEXT.value)
    bind_cfg = MenuBinding(
        schema="unknown",
        target=TextTarget(content="context.content"),
    )
    binding = mock_binder.binding(bind_cfg, ctx)
    assert isinstance(binding, TextBinding)
    assert mock_binder.binding(None, ctx) is None