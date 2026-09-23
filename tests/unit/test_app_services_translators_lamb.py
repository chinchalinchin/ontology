"""
# Ontology: tests.unit.test_app_services_translators_lamb
"""
import pytest
from unittest.mock import MagicMock
from app.services.translators.lamb import LambdaTranslator, LambdaExecutor

def test_lambda_compiles_successfully(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    assert isinstance(executor, LambdaExecutor)
    assert "idle" in executor.transitions
    assert len(executor.transitions["idle"]) == 2
    assert executor.transitions["idle"][0].next == "attack"

def test_lambda_evaluation_matches_first_condition(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = MagicMock()
    sprite_mock.health = 30
    
    result = executor.evaluate("idle", {"sprite": sprite_mock})
    assert result == "attack"

def test_lambda_evaluation_matches_second_condition(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = MagicMock()
    sprite_mock.health = 60
    
    result = executor.evaluate("idle", {"sprite": sprite_mock})
    assert result == "wander"

def test_lambda_evaluation_with_dictionary_lookup(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    enemy_mock = MagicMock()
    enemy_mock.dead = True
    
    result = executor.evaluate("attack", {"sprites": {"enemy": enemy_mock}})
    assert result == "idle"

def test_lambda_evaluation_with_plot_metadata(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    plot_mock = MagicMock()
    plot_mock.mayor_bribed = True
    
    result = executor.evaluate("town-locked", {"plot": plot_mock})
    assert result == "town-unlocked"

def test_lambda_evaluation_attribute_error_handling(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = object() 
    
    result = executor.evaluate("idle", {"sprite": sprite_mock})
    assert result is None
    
def test_lambda_evaluation_with_environ_functions(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = MagicMock()
    sprite_mock.pos.x = 0
    sprite_mock.pos.y = 0
    
    target_mock = MagicMock()
    target_mock.pos.x = 5
    target_mock.pos.y = 5
    
    # Pass 'target' inside the standard 'sprites' ISL namespace
    result = executor.evaluate("find", {"sprite": sprite_mock, "sprites": {"target": target_mock}})
    assert result == "interact"
    
def test_lambda_evaluation_unknown_state(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    result = executor.evaluate("unknown", {})
    assert result is None

def test_lambda_ignores_bad_syntax(mock_intention_configuration):
    translator = LambdaTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    assert len(executor.transitions["bad_syntax"][0].conditions) == 0