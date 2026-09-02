"""
# Ontology: tests.unit.test_app_services_migrator
"""
from unittest.mock import MagicMock, patch
from app.services.migrator import Migrator

def test_migrator_no_target():
    migrator = Migrator(MagicMock(), MagicMock(), MagicMock())
    # Should return True instantly if no target is set
    assert migrator.step(budget_ms=16) is True

@patch('app.services.migrator.time.perf_counter')
def test_migrator_time_slicing(mock_perf_counter):
    migrator = Migrator(MagicMock(), MagicMock(), MagicMock())
    migrator.target = "test-level"
    
    # Create a fake generator that yields 3 times
    def fake_gen():
        yield True
        yield True
        yield True
        
    migrator._build_generator = MagicMock(return_value=fake_gen())
    
    # 1st step: simulate exceeding budget immediately after 1st yield
    # perf_counter will be called: start, then inside the loop
    mock_perf_counter.side_effect = [0.0, 1.0, 2.0] # 1.0s diff = 1000ms > 16ms
    
    assert migrator.step(budget_ms=16) is False
    
    # 2nd step: process the remaining 2 yields without exceeding the budget
    mock_perf_counter.side_effect = [0.0, 0.001, 0.002, 0.003, 0.004]
    
    assert migrator.step(budget_ms=16) is True
    assert migrator.target is None
    assert migrator._generator is None

@patch('app.services.migrator.dataclasses.fields')
@patch('app.services.migrator.Loader.load_state')
@patch('app.services.migrator.Decomposer')
def test_migrator_build_generator(mock_decomposer, mock_load_state, mock_fields):
    mock_board = MagicMock()
    mock_props = MagicMock()
    mock_configs = MagicMock()
    
    # Setup mock state with some compositions and normal assets
    mock_state_magic = MagicMock()
    mock_state_magic.compositions = ["comp1", "comp2"]
    mock_load_state.return_value = mock_state_magic
    
    # Skip normal assets iteration for this test
    mock_fields.return_value = []
    
    migrator = Migrator(mock_board, mock_props, mock_configs)
    migrator.target = "test-level"
    
    gen = migrator._build_generator()
    
    # Run generator to completion
    for _ in gen:
        pass
        
    # Board should have had `add()` called for the unpacked compositions
    assert mock_board.add.called
    assert migrator.maximum >= 1

@patch('app.services.migrator.Loader.load_state')
@patch('app.services.migrator.Decomposer')
def test_migrator_build_generator_assets(mock_decomposer, mock_load_state, mock_state):
    mock_board = MagicMock()
    mock_props = MagicMock()
    mock_configs = MagicMock()
    
    # Use real mock_state from conftest (StateSchema with 1 Sprite)
    mock_load_state.return_value = mock_state
    
    migrator = Migrator(mock_board, mock_props, mock_configs)
    migrator.target = "world-01"
    
    gen = migrator._build_generator()
    for _ in gen:
        pass
        
    assert mock_board.add.called
    assert migrator.maximum >= 1