# /home/grant/Projects/ontology/tests/unit/test_app_services_generators_binder.py

import pytest
from unittest.mock import MagicMock

from app.services.generators.binder import Binder
from app.game.menus.bindings import (
    LibraryBinding, 
    MeterBinding, 
    IconBinding, 
    SelectBinding, 
    TextBinding
)

@pytest.fixture
def binder():
    return Binder(registry=MagicMock(), library=MagicMock())

def test_binding_library(binder):
    bind_cfg = MagicMock()
    bind_cfg.schema = 'library'
    bind_cfg.target = 'context.sprite.state'
    
    binding = binder.binding(bind_cfg, {'sprite': {'state': {}}})
    assert isinstance(binding, LibraryBinding)

def test_binding_meter(binder):
    bind_cfg = MagicMock()
    bind_cfg.schema = 'meter'
    bind_cfg.target = 'context.hp'
    
    binding = binder.binding(bind_cfg, {'hp': {}})
    assert isinstance(binding, MeterBinding)

def test_binding_icon(binder):
    bind_cfg = MagicMock()
    bind_cfg.schema = 'icon'
    bind_cfg.target = 'context.item'
    
    binding = binder.binding(bind_cfg, {'item': {}})
    assert isinstance(binding, IconBinding)

def test_binding_select(binder):
    bind_cfg = MagicMock()
    bind_cfg.schema = 'select'
    bind_cfg.selection = 'scrollup'
    bind_cfg.selector = 'my_page'
    
    binding = binder.binding(bind_cfg, {})
    assert isinstance(binding, SelectBinding)
    assert binding.selection == 'scrollup'
    assert binding.selector == 'my_page'

def test_binding_fallback_text(binder):
    bind_cfg = MagicMock()
    bind_cfg.schema = 'unknown'
    bind_cfg.target = 'context.text'
    
    binding = binder.binding(bind_cfg, {'text': 'hello'})
    assert isinstance(binding, TextBinding)

def test_binding_none(binder):
    assert binder.binding(None, {}) is None