"""
@domain.test
@test.unit
@app.services
@workflow.injection

# Ontology: tests.unit.app.services.orchestration.test_builder

Unit tests for the Builder class.
"""
# Standard Libraries
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
from app.static.semantics import Devices

# Cython Libraries
from libs.core.models import Dimensions

# ------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_injection,
]

# ------------------------------------------------------------------


def test_builder_load_data(mock_builder):
    mock_builder.load_data()

    assert mock_builder.context.properties is not None
    assert mock_builder.context.configurations is not None


@patch("app.services.orchestration.builder.render")
def test_builder_init_subsystems(mock_render, mock_builder):
    dims = Dimensions(w=1280, l=720)
    mock_builder.init_subsystems(dims, headless=False)

    assert mock_builder.context.screensize == dims
    assert mock_builder.context.headless is False
    mock_render.init.assert_called_once_with(1280, 720, False)
    mock_render.show.assert_called_once()


def test_builder_build_services(mock_builder):
    mock_builder.load_data()
    mock_builder.build_relations()
    mock_builder.build_services(Devices.KEYBOARD.value)

    assert mock_builder.device is not None
    assert mock_builder.decomposer is not None
    assert mock_builder.cradle is not None
    assert mock_builder.materializer is not None
    assert mock_builder.provider is not None
    assert mock_builder.device.poll() is not None


def test_builder_build_board(mock_builder):
    mock_builder.load_data()
    mock_builder.build_relations()
    mock_builder.build_services(Devices.KEYBOARD.value)
    mock_builder.build_board()

    assert mock_builder.board is not None
    assert mock_builder.board.loaded is False
    assert len(mock_builder.board.assets()) == 0
    assert mock_builder.board.cradle is mock_builder.cradle
    assert mock_builder.board.device is mock_builder.device
    assert mock_builder.board.migrator is not None