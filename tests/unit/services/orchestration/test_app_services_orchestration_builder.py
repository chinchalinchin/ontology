"""
# Ontology: tests.unit.test_app_services_constructors
"""
# Standard Libraries
from unittest.mock import patch

# Application Libraries
from app.config.enums import Devices

# Cython Libraries
from libs.core.models import Dimensions

def test_builder_load_data(mock_builder):
    mock_builder.load_data("world-01")
    
    assert mock_builder.context.properties is not None
    assert mock_builder.context.configurations is not None
    assert mock_builder.context.state is not None

@patch('app.services.orchestration.builder.render')
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
    assert mock_builder.board.loaded is False
    # Board initializes completely empty, deferred to Migrator
    assert len(mock_builder.board.assets()) == 0
    assert mock_builder.decomposer is not None

def test_builder_build_services(mock_builder):
    # Setup prerequisite context
    mock_builder.load_data("world-01")
    mock_builder.build_board()
    
    mock_builder.build_services(Devices.KEYBOARD.value)
    
    assert mock_builder.board.cradle is not None
    # Ensure the keyboard mapping from configuration was applied
    assert mock_builder.board.device.poll() is not None
