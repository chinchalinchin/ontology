"""
# Ontology: tests.unit.app.services.orchestration.test_migrator
"""
# Standard Libraries
import dataclasses
from unittest.mock import patch

# External Libraries
import pytest

# Application Libraries
import app.config.settings as settings
from app.models.state.assets.objects import PropertyState


@pytest.mark.orchestration
def test_migrator_no_target(mock_migrator):
    assert mock_migrator.step(budget_ms=16) is True


@pytest.mark.orchestration
@patch.object(settings, 'SEPARATOR', new='-')
@patch('app.services.orchestration.migrator.time.perf_counter')
@patch('app.services.orchestration.migrator.Loader.load_state')
def test_migrator_time_slicing(
    mock_load_state, 
    mock_perf_counter, 
    mock_migrator, 
    mock_state
):
    # Clone an existing valid sprite state to preserve layer assignment
    base_sprite = mock_state.sheets.sprites[0]
    mock_state.sheets.sprites.append(
        dataclasses.replace(base_sprite, name="sprite_clone_1")
    )
    mock_load_state.return_value = mock_state
    mock_migrator.target = "world-01"

    # Step 1: exceed budget after first iteration (start=0.0, check1=0.001 -> executes task, check2=1.0 -> 1000ms > 16ms)
    mock_perf_counter.side_effect = [0.0, 0.001, 1.0]
    assert mock_migrator.step(budget_ms=16) is False
    assert mock_migrator.target == "world-01"
    assert mock_migrator._generator is not None
    assert mock_migrator.current >= 1

    # Step 2: process remaining tasks within budget
    mock_perf_counter.side_effect = [0.0] + [0.001 * i for i in range(1, 20)]
    assert mock_migrator.step(budget_ms=16) is True
    assert mock_migrator.target is None
    assert mock_migrator._generator is None
    assert mock_migrator.current == mock_migrator.maximum


@pytest.mark.orchestration
@patch.object(settings, 'SEPARATOR', new='-')
@patch('app.services.orchestration.migrator.Loader.load_state')
def test_migrator_build_generator_compositions(
    mock_load_state, 
    mock_migrator, 
    mock_state
):
    mock_state.compositions = [
        PropertyState(
            id="brick-house", 
            name="house_instance", 
            layer="0"
        )
    ]
    mock_load_state.return_value = mock_state
    mock_migrator.target = "world-01"

    initial_asset_count = len(mock_migrator.board.assets())
    gen = mock_migrator._build_generator()
    for _ in gen:
        pass

    assert len(mock_migrator.board.assets()) > initial_asset_count
    assert mock_migrator.maximum >= 1


@pytest.mark.orchestration
@patch.object(settings, 'SEPARATOR', new='-')
@patch('app.services.orchestration.migrator.Loader.load_state')
def test_migrator_build_generator_assets(mock_load_state, mock_migrator, mock_state):
    mock_load_state.return_value = mock_state
    mock_migrator.target = "world-01"

    initial_asset_count = len(mock_migrator.board.assets())
    gen = mock_migrator._build_generator()
    for _ in gen:
        pass

    assert len(mock_migrator.board.assets()) > initial_asset_count
    assert mock_migrator.maximum >= 1