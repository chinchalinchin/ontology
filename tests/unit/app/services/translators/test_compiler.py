"""
# Ontology: tests.unit.app.services.translators.test_app_services_translators_compiler
"""
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
def test_compiler_evaluation_matches_first_condition(mock_intention_configuration, mock_sprite_state):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    mock_sprite_state.meters.health.current = 30
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_sprite_state}
    )
    assert result == Intentions.ATTACK.value


@pytest.mark.intentions
def test_compiler_evaluation_matches_second_condition(mock_intention_configuration, mock_sprite_state):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    mock_sprite_state.meters.health.current = 60
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_sprite_state}
    )
    assert result == Intentions.WANDER.value


@pytest.mark.intentions
def test_compiler_evaluation_with_dictionary_lookup(mock_intention_configuration, mock_sprite_state_alt):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    mock_sprite_state_alt.mutators.triggers.dead = True
    
    result = executor.evaluate(
        Intentions.ATTACK.value, 
        {"sprites": {"enemy": mock_sprite_state_alt}}
    )
    assert result == Intentions.IDLE.value


@pytest.mark.plots
def test_compiler_evaluation_with_plot_metadata(mock_plot_configuration, mock_plot_state):
    translator = CompilerTranslator()
    executor = translator.compile(mock_plot_configuration)
    
    mock_plot_state.previous.append("mayor_bribed")
    
    result = executor.evaluate("town-locked", {"plot": mock_plot_state})
    assert result == "town-unlocked"


@pytest.mark.intentions
def test_compiler_evaluation_attribute_error_handling(mock_intention_configuration, mock_positional_state):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    # PositionalState has no 'meters' attribute, so 'sprite.meters.health.current' safely trips AttributeError handling
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_positional_state}
    )
    assert result is None


@pytest.mark.intentions
def test_compiler_evaluation_with_environ_functions(
    mock_intention_configuration, 
    mock_sprite_state, 
    mock_sprite_state_alt
):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    mock_sprite_state.goal.name = "npc"
    mock_sprite_state.position.x = 0
    mock_sprite_state.position.y = 0
    
    mock_sprite_state_alt.position.x = 5
    mock_sprite_state_alt.position.y = 5
    
    # Provide a simple explicit runtime stub for environmental function injections 
    class _MockFunctions:
        def is_near(self, p1, p2, dist):
            return True

    result = executor.evaluate(
        Intentions.FIND.value, 
        {
            "sprite": mock_sprite_state, 
            "sprites": {"npc": mock_sprite_state_alt},
            "functions": _MockFunctions()
        }
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