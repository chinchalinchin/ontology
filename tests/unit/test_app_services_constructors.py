"""
# Ontology: tests.unit.test_app_services_constructors
"""
import pytest
from unittest.mock import patch
from app.config.enums import Devices
from libs.core.models import Dimensions

def test_builder_load_data(mock_builder):
    mock_builder.load_data("world-01")
    
    assert mock_builder.context.properties is not None
    assert mock_builder.context.configurations is not None
    assert mock_builder.context.state is not None

@patch('app.services.constructors.render')
def test_builder_init_subsystems(mock_render, mock_builder):
    dims = Dimensions(w=1280, l=720)
    mock_builder.init_subsystems(dims, headless=False)
    
    assert mock_builder.context.screensize == dims
    assert mock_builder.context.headless is False
    mock_render.init.assert_called_once_with(1280, 720, False)
    mock_render.show.assert_called_once()

def test_builder_build_board(mock_builder):
    # Setup prerequisite context
    mock_builder.load_data("world-01")
    mock_builder.build_board()
    
    assert mock_builder.board is not None
    assert mock_builder.board.loaded is True
    # mock_state contains exactly 1 sprite asset
    assert len(mock_builder.board.assets()) == 1
    assert mock_builder.decomposer is not None

def test_builder_build_services(mock_builder):
    # Setup prerequisite context
    mock_builder.load_data("world-01")
    mock_builder.build_board()
    
    mock_builder.build_services(Devices.KEYBOARD)
    
    assert mock_builder.board.cradle is not None
    # Ensure the keyboard mapping from configuration was applied
    assert mock_builder.board.device.poll() is not None

@patch('app.services.constructors.Screen')
@patch('app.services.constructors.Registry')
@patch('app.services.constructors.render')
def test_orchestrator_construct(mock_render, mock_registry, mock_screen, mock_orchestrator):
    dims = Dimensions(w=1280, l=720)
    
    # The director should enforce the execution of all builder steps
    engine = mock_orchestrator.orchestrate(
        state_key="world-01", 
        screensize=dims, 
        device=Devices.KEYBOARD, 
        headless=True
    )
    
    assert engine is not None
    assert engine.board is not None
    assert engine.board.loaded is True
    
    # Mechanics lists should fall back to defaults when not explicitly configured
    assert len(engine.core) == 3
    assert len(engine.world) == 2
    
    # Verify Cython SDL boundary layer was initialized correctly
    mock_render.init.assert_called_once_with(1280, 720, True)
    # render.show() should NOT be called in headless mode
    mock_render.show.assert_not_called()
    mock_registry.assert_called_once()