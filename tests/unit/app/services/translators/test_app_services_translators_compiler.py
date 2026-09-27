"""
# Ontology: tests.unit.services.translators.test_app_services_translators_compiler
"""
# Standard Libraries
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
from app.config.enums import Intentions
from app.services.translators.compiler import (
    CompilerTranslator, 
    CompilerExecutor
)

@pytest.mark.intentions
def test_compiler_compiles_successfully(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    assert isinstance(executor, CompilerExecutor)
    assert Intentions.IDLE.value in executor.transitions
    assert len(executor.transitions[Intentions.IDLE.value]) == 2
    assert executor.transitions[Intentions.IDLE.value][0].next == Intentions.ATTACK.value


@pytest.mark.intentions
def test_compiler_evaluation_matches_first_condition(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = MagicMock()
    sprite_mock.health = 30
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": sprite_mock}
    )
    assert result == Intentions.ATTACK.value


@pytest.mark.intentions
def test_compiler_evaluation_matches_second_condition(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = MagicMock()
    sprite_mock.health = 60
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": sprite_mock}
    )
    assert result == Intentions.WANDER.value


@pytest.mark.intentions
def test_compiler_evaluation_with_dictionary_lookup(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    enemy_mock = MagicMock()
    enemy_mock.dead = True
    
    result = executor.evaluate(
        Intentions.ATTACK.value, 
        {"sprites": {"enemy": enemy_mock}}
    )
    assert result == Intentions.IDLE.value


@pytest.mark.plots
def test_compiler_evaluation_with_plot_metadata(mock_plot_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_plot_configuration)
    
    plot_mock = MagicMock()
    plot_mock.mayor_bribed = True
    
    result = executor.evaluate("town-locked", {"plot": plot_mock})
    assert result == "town-unlocked"


@pytest.mark.intentions
def test_compiler_evaluation_attribute_error_handling(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = object() 
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": sprite_mock}
    )
    assert result is None


@pytest.mark.intentions
def test_compiler_evaluation_with_environ_functions(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    sprite_mock = MagicMock()
    sprite_mock.pos.x = 0
    sprite_mock.pos.y = 0
    
    target_mock = MagicMock()
    target_mock.pos.x = 5
    target_mock.pos.y = 5
    
    # Pass 'target' inside the standard 'sprites' ISL namespace 
    result = executor.evaluate(
        Intentions.FIND.value, 
        {"sprite": sprite_mock, "sprites": {"target": target_mock}}
    )
    assert result == Intentions.INTERACT.value


@pytest.mark.intentions
def test_compiler_evaluation_unknown_state(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    result = executor.evaluate("unknown", {})
    assert result is None
 

@pytest.mark.intentions
def test_compiler_ignores_bad_syntax(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    assert len(executor.transitions["bad_syntax"][0].conditions) == 0