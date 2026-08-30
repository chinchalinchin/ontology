"""
# Ontology: tests.unit.test_app_hooks_orchestrator
"""
import pytest
from unittest.mock import patch
from app.config.enums import Devices
from libs.core.models import Dimensions

def test_orchestrator_initialization(mock_orchestrator):
    assert mock_orchestrator.properties is not None
    assert mock_orchestrator.configurations is not None
    assert mock_orchestrator.state is not None
    assert mock_orchestrator.decomposer is not None

def test_orchestrator_migrate(mock_orchestrator):
    board = mock_orchestrator.migrate()
    
    assert board is not None
    assert board.loaded is True
    # mock_state contains exactly 1 sprite asset
    assert len(board.assets()) == 1

def test_orchestrator_inject(mock_orchestrator):
    mock_orchestrator.migrate()
    board = mock_orchestrator.inject(Devices.KEYBOARD)
    
    assert board.cradle is not None
    # Ensure the keyboard mapping from configuration was applied
    assert board.device.poll() is not None

@patch('app.hooks.orchestrator.Screen')
@patch('app.hooks.orchestrator.Registry')
@patch('app.hooks.orchestrator.render')
def test_orchestrator_ignite(mock_render, mock_registry, mock_screen, mock_orchestrator):
    dims = Dimensions(w=1280, l=720)
    engine = mock_orchestrator.ignite(dims, Devices.KEYBOARD)
    
    assert engine is not None
    assert engine.board is not None
    
    # Mechanics lists should fall back to defaults when empty
    assert len(engine.core) == 3
    assert len(engine.world) == 2
    
    # Verify Cython SDL boundary layer was initialized
    mock_render.init.assert_called_once_with(1280, 720, False)
    mock_registry.assert_called_once()