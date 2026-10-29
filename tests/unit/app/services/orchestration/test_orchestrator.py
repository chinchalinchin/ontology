"""
@domain.test
@test.unit
@app.services
@workflow.injection

# Ontology: Tests - tests.unit.app.services.orchestration.test_orchestrator

Unit tests for the Orchestrator class.
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    Devices,
    Menus,
)
from app.game.menus.events import (
    MenuEvent,
    StateEvent,
)

# Cython Libraries
from libs.core.models import Dimensions

# ------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_injection,
]

# ------------------------------------------------------------------


@patch("app.services.orchestration.builder.Screen")
@patch("app.services.orchestration.builder.render")
def test_orchestrator_construct(
    mock_render,
    mock_screen,
    mock_orchestrator,
    testbed,
):
    dims = Dimensions(w=1280, l=720)

    engine = mock_orchestrator.orchestrate(
        state_key=testbed,
        screensize=dims,
        device=Devices.KEYBOARD.value,
        headless=True,
    )

    mech_cfg = mock_orchestrator.builder.context.configurations.mechanics

    assert engine is not None
    assert engine.board is not None
    assert engine.board.loaded is False
    assert len(engine.core) == len(mech_cfg.core)
    assert len(engine.world) == len(mech_cfg.world)

    # Verify Cython SDL boundary layer was initialized correctly
    mock_render.init.assert_called_once_with(1280, 720, True)
    mock_render.show.assert_not_called()
    mock_screen.assert_called_once()

    # State key triggers direct state hydration event
    assert len(engine.bus) == 1
    assert isinstance(engine.bus[0], StateEvent)
    assert engine.bus[0].id == testbed


@patch("app.services.orchestration.builder.Screen")
@patch("app.services.orchestration.builder.render")
def test_orchestrator_construct_main_menu(
    mock_render,
    mock_screen,
    mock_orchestrator,
):
    dims = Dimensions(w=1280, l=720)

    # Omission of state_key routes directly to Main Menu
    engine = mock_orchestrator.orchestrate(
        state_key=None,
        screensize=dims,
        device=Devices.KEYBOARD.value,
        headless=True,
    )

    assert engine is not None
    assert engine.board is not None
    assert engine.board.loaded is False

    assert len(engine.bus) == 1
    assert isinstance(engine.bus[0], MenuEvent)
    assert engine.bus[0].id == Menus.MAIN.value