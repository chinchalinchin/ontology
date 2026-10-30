"""
@domain.test
@test.unit
@app.services
@workflow.intentions
@workflow.plots
@workflow.seasons
@workflow.transitions

# Ontology: Tests - tests.unit.app.services.translators.test_compiler

Unit tests for the Compiler implementation of Transition Translation.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Intentions,
    Translators,
    Goals
)
from app.models.state.assets.sheets import Goal
from app.services.translators.compiler import (
    CompilerTranslator, 
    CompilerExecutor,
)
from app.services.translators.lamb import (
    LambdaTranslator,
    LambdaExecutor
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_transitions
]

# -----------------------------------------------------

@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_compiles_successfully(
    implementation,
    mock_translator,
    mock_configurations_schema
):
    translator = mock_translator(implementation[0])
    executor = translator.compile(mock_configurations_schema.intentions)
    
    assert isinstance(executor, implementation[1])
    assert Intentions.IDLE.value in executor.transitions
    assert len(executor.transitions[Intentions.IDLE.value]) == 5
    assert executor.transitions[Intentions.IDLE.value][0].next == Intentions.WANDER.value


@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_intention_executor_evaluation_matches_wander(
    implementation,
    mock_translator,
    mock_configurations_schema,
    mock_state
):
    translator = mock_translator(implementation[0])
    executor = translator.compile(mock_configurations_schema.intentions)

    mock_sprite_state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value
    )
    mock_sprite_state.goal = Goal(
        category = Goals.POSITION.value,
        layer = mock_sprite_state.layer
    )
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_sprite_state}
    )
    assert result == Intentions.WANDER.value


@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_intention_executor_matches_hunt(
    implementation,
    mock_translator,
    mock_configurations_schema,
    mock_state
):
    translator = mock_translator(implementation[0])
    executor = translator.compile(mock_configurations_schema.intentions)

    mock_sprite_state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value
    )
    mock_sprite_state.goal = Goal(
        category = Goals.TARGET.value,
        layer = mock_sprite_state.layer
    )
    
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_sprite_state}
    )
    assert result == Intentions.HUNT.value


@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_compiler_evaluation_with_dictionary_lookup(
    implementation,
    mock_translator,
    mock_configurations_schema,
    mock_state
):
    translator = mock_translator(implementation[0])
    executor = translator.compile(mock_configurations_schema.intentions)

    mock_sprite_state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value    
    )
    mock_sprite_state.goal = Goal(
        name = "enemy",
        category = Goals.TARGET.value,
        layer = mock_sprite_state.layer,
    )

    mock_enemy_state = mock_state(
        AssetCategories.SHEETS.value,
        AssetInstances.SPRITES.value,
        name="enemy"
    )
    mock_enemy_state.mutators.triggers.dead = True
        
    result = executor.evaluate(
        Intentions.ATTACK.value, 
        {   
            "sprite": mock_sprite_state,
            "sprites": {"enemy": mock_enemy_state }
        }
    )
    assert result == Intentions.SCAVENGE.value


@pytest.mark.workflow_plots
def test_compiler_evaluation_with_plot_metadata(mock_plot_configuration, mock_plot_state):
    translator = CompilerTranslator()
    executor = translator.compile(mock_plot_configuration)
    
    mock_plot_state.previous.append("mayor_bribed")
    
    result = executor.evaluate("town-locked", {"plot": mock_plot_state})
    assert result == "town-unlocked"


@pytest.mark.workflow_intentions
def test_compiler_evaluation_attribute_error_handling(mock_intention_configuration, mock_positional_state):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    # MotiveState has no 'meters' attribute, so 'sprite.meters.health.current' safely trips AttributeError handling
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_positional_state}
    )
    assert result is None


@pytest.mark.workflow_intentions
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


@pytest.mark.workflow_intentions
def test_compiler_evaluation_unknown_state(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    result = executor.evaluate("unknown", {})
    assert result is None
 

@pytest.mark.workflow_intentions
def test_compiler_ignores_bad_syntax(mock_intention_configuration):
    translator = CompilerTranslator()
    executor = translator.compile(mock_intention_configuration)
    
    assert len(executor.transitions["bad_syntax"][0].conditions) == 0