"""
# Ontology: tests.unit.test_app_services_generators_menus_binder
"""
from unittest.mock import MagicMock
import pytest

from app.services.generators.menus.binder import Binder
from app.game.menus.bindings import (
    LibraryBinding, 
    MeterBinding, 
    IconBinding, 
    SelectBinding, 
    TextBinding,
    CollectionBinding,
    ApertureBinding
)
from app.config.enums import Bindings
from app.models.config.menus import MenuBinding
from app.models.state.widgets import CollectionState


@pytest.fixture
def binder():
    mock_registry = MagicMock()
    mock_registry.font.return_value = MagicMock()
    return Binder(registry=mock_registry, library=MagicMock())


def test_binding_library(binder):
    bind_cfg = MenuBinding(schema=Bindings.LIBRARY.value, target={'plot': 'context.plot'})
    binding = binder.binding(bind_cfg, {'plot': {}})
    
    assert isinstance(binding, LibraryBinding)
    assert binding.registry == binder.registry
    assert binding.library == binder.library


def test_binding_meter(binder):
    bind_cfg = MenuBinding(schema=Bindings.METER.value, target={'meter': 'context.hp'})
    binding = binder.binding(bind_cfg, {'hp': {}})
    assert isinstance(binding, MeterBinding)


def test_binding_icon(binder):
    bind_cfg = MenuBinding(schema=Bindings.ICON.value, target={'icon': 'context.item'})
    binding = binder.binding(bind_cfg, {'item': {}})
    assert isinstance(binding, IconBinding)


def test_binding_select(binder):
    bind_cfg = MenuBinding(
        schema=Bindings.SELECT.value, 
        target={'selection': 'scrollup', 'selector': 'my_page'}
    )
    binding = binder.binding(bind_cfg, {})
    assert isinstance(binding, SelectBinding)
    assert binding.selection == 'scrollup'
    assert binding.selector == 'my_page'


def test_binding_collection(binder):
    bind_cfg = MenuBinding(
        schema=Bindings.COLLECTION.value,
        target={'source': 'context.inventory.pack', 'capacity': '8', 'columns': '4'}
    )
    binding = binder.binding(bind_cfg, {'inventory': {'pack': ['sword']}})
    assert isinstance(binding, CollectionBinding)


def test_binding_aperture(binder):
    mock_pane = MagicMock()
    mock_pane.state = CollectionState(
        collection_function=lambda: ["shortsword", "dagger"],
        capacity=8,
        columns=4
    )
    widgets = {"inventory-pack-grid": mock_pane}

    bind_cfg = MenuBinding(
        schema=Bindings.APERTURE.value,
        target={'selector': 'inventory-pack-grid', 'index': '0'}
    )
    binding = binder.binding(bind_cfg, {}, widgets=widgets)
    
    assert isinstance(binding, ApertureBinding)
    assert binding.get_item() == "shortsword"

    # Vacant slot evaluation returns empty string
    vacant_cfg = MenuBinding(
        schema=Bindings.APERTURE.value,
        target={'selector': 'inventory-pack-grid', 'index': '5'}
    )
    vacant_binding = binder.binding(vacant_cfg, {}, widgets=widgets)
    assert vacant_binding.get_item() == ""


def test_binding_fallback_text(binder):
    bind_cfg = MenuBinding(schema='unknown', target={'content': 'context.text'})
    binding = binder.binding(bind_cfg, {'text': 'hello'})
    assert isinstance(binding, TextBinding)


def test_binding_none(binder):
    assert binder.binding(None, {}) is None