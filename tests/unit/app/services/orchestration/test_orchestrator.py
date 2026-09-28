"""
# Ontology: tests.unit.app.services.orchestration.test_orchestrator
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
from app.config.enums import Devices

# Cython Libraries
from libs.core.models import Dimensions

@pytest.mark.orchestration
@patch('app.services.orchestration.builder.Screen')
@patch('app.services.orchestration.builder.render')
def test_orchestrator_construct(
    mock_render, 
    mock_registry, 
    mock_orchestrator
):
    dims = Dimensions(w=1280, l=720)
    
    # The director should enforce the execution of all builder steps
    engine = mock_orchestrator.orchestrate(
        state_key="world-01", 
        screensize=dims, 
        device=Devices.KEYBOARD.value, 
        headless=True
    )
    
    assert engine is not None
    assert engine.board is not None
    assert engine.board.loaded is False
    
    
    assert len(engine.core) == 3
    assert len(engine.world) == 2
    
    # Verify Cython SDL boundary layer was initialized correctly
    mock_render.init.assert_called_once_with(1280, 720, True)
    # render.show() should NOT be called in headless mode
    mock_render.show.assert_not_called()
    mock_registry.assert_called_once()