"""
# Ontology: tests.unit.test_app_services_generators_menus_binder
"""
# Standard Libraries
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
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


@pytest.mark.menus
def test_binding_library(mock_binder, mock_library_bind):
    binding = mock_binder.binding(
        mock_library_bind, 
        {'plot': {}}
    )
    
    assert isinstance(binding, LibraryBinding)
    assert binding.registry == mock_binder.registry
    assert binding.library == mock_binder.library


@pytest.mark.menus
def test_binding_meter(mock_binder, mock_meter_bind):
    binding = mock_binder.binding(mock_meter_bind, {'health': {}})
    assert isinstance(binding, MeterBinding)


@pytest.mark.menus
def test_binding_icon(mock_binder, mock_icon_bind):
    binding = mock_binder.binding(mock_icon_bind, {'item': {}})
    assert isinstance(binding, IconBinding)


@pytest.mark.menus
def test_binding_select(mock_binder, mock_select_bind):
    binding = mock_binder.binding(mock_select_bind, {})
    assert isinstance(binding, SelectBinding)
    assert binding.selection == mock_select_bind.target['selection']
    assert binding.selector == mock_select_bind.target['selector']


@pytest.mark.menus
def test_binding_collection(mock_binder, mock_collection_bind):
    binding = mock_binder.binding(mock_collection_bind, {'inventory': {'pack': ['sword']}})
    assert isinstance(binding, CollectionBinding)


@pytest.mark.menus
def test_binding_aperture(
    mock_binder, 
    mock_collection_state,
    mock_aperture_bind,
):
    mock_pane = MagicMock()
    mock_pane.state = mock_collection_state
    widgets = {"inventory-pack-grid": mock_pane}

    binding = mock_binder.binding(mock_aperture_bind, {}, widgets=widgets)
    
    assert isinstance(binding, ApertureBinding)
    assert binding.get_item() == "shortsword"


@pytest.mark.menus
def test_binding_aperture_vacant(
    mock_binder, 
    mock_collection_state,
    mock_aperture_bind_alt
):
    mock_pane = MagicMock()
    mock_pane.state = mock_collection_state
    widgets = {"inventory-pack-grid": mock_pane}

    # Vacant slot evaluation returns empty string
    vacant_binding = mock_binder.binding(mock_aperture_bind_alt, {}, widgets=widgets)
    assert vacant_binding.get_item() == ""


@pytest.mark.menus
def test_binding_fallback_text(mock_binder):
    bind_cfg = MenuBinding(
        schema='unknown', 
        target={'content': 'context.text'}
    )
    binding = mock_binder.binding(bind_cfg, {'text': 'hello'})
    assert isinstance(binding, TextBinding)


@pytest.mark.menus
def test_binding_none(mock_binder):
    assert mock_binder.binding(None, {}) is None