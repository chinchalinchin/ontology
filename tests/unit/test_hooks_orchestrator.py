"""
# Ontology: tests.unit.test_hooks_orchestrator
"""
import pytest
from unittest.mock import patch
from app.hooks.orchestrator import Orchestrator
from app.config.enums import Devices
from libs.core.models import Dimensions

@pytest.fixture
def orchestrator(mock_properties, mock_configurations, mock_state):
    # Patch the loader before initializing the orchestrator so it doesn't touch the filesystem
    with patch('app.hooks.orchestrator.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Orchestrator(state="world-01")

def test_orchestrator_initialization(orchestrator):
    assert orchestrator.properties is not None
    assert orchestrator.configurations is not None
    assert orchestrator.state is not None
    assert orchestrator.decomposer is not None

def test_orchestrator_migrate(orchestrator):
    board = orchestrator.migrate()
    
    assert board is not None
    assert board.loaded is True
    # mock_state contains exactly 1 sprite asset
    assert len(board.assets()) == 1

def test_orchestrator_inject(orchestrator):
    orchestrator.migrate()
    board = orchestrator.inject(Devices.KEYBOARD)
    
    assert board.cradle is not None
    # Ensure the keyboard mapping from configuration was applied
    assert board.poll() is not None

@patch('app.hooks.orchestrator.Screen')
@patch('app.hooks.orchestrator.Registry')
@patch('app.hooks.orchestrator.render')
def test_orchestrator_ignite(mock_render, mock_registry, mock_screen, orchestrator):
    dims = Dimensions(w=1280, l=720)
    engine = orchestrator.ignite(dims, Devices.KEYBOARD)
    
    assert engine is not None
    assert engine.board is not None
    # Mechanics list should fall back to default when empty
    assert len(engine.mechanics) == 4 
    
    # Verify Cython SDL boundary layer was initialized
    mock_render.init.assert_called_once_with(1280, 720, False)
    mock_registry.assert_called_once()