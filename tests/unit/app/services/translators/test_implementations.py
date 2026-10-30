"""
@domain.test
@test.unit
@app.services
@workflow.intentions
@workflow.plots
@workflow.seasons
@workflow.transitions

# Ontology: Tests - tests.unit.app.services.translators.test_implementations

Unit tests for the implementations of the Transition Translation subsystem.
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
from app.services.translators.base import Transition
from app.services.translators.compiler import (
    CompilerExecutor,
)
from app.services.translators.lamb import (
    LambdaExecutor
)

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_transitions
]

# -----------------------------------------------------

@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_compiles(
    implementation,
    mock_translator,
    mock_configurations_schema
):
    translator = mock_translator(implementation[0])
    executor = translator.compile(mock_configurations_schema.intentions)
    
    assert isinstance(executor, implementation[1])


@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_compiles_intentions(
    implementation,
    mock_translator,
    mock_configurations_schema
):
    translator = mock_translator(implementation[0])
    executor = translator.compile(mock_configurations_schema.intentions)
    
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
def test_executor_evaluation_with_dictionary_lookup(
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
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_evaluation_with_plot_metadata(
    implementation,
    mock_translator,
    mock_configurations_schema,
    mock_state_schema
):
    translator = mock_translator(implementation[0])    
    executor = translator.compile(mock_configurations_schema.plots)

    mock_player_state = mock_state_schema.sheets.players[0]
    mock_plot_state = mock_state_schema.plots
    mock_player_state.inventory.pack['writ-of-dawn'] = 1
    
    result = executor.evaluate(mock_plot_state.current, 
        { 
            "plot": mock_plot_state ,
            "sprites": { "player": mock_player_state } 
        }
    )
    assert result == "castle-dawn-unlocked"


@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_evaluation_attribute_error_handling(
    implementation,
    mock_configurations_schema,
    mock_translator,
    mock_state
):
    translator = mock_translator(implementation[0])  
    executor = translator.compile(mock_configurations_schema.intentions)

    mock_crate_state = mock_state(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value
    )
    # MotiveState has no 'meters' attribute, so 'sprite.meters.health.current' safely trips AttributeError handling
    result = executor.evaluate(
        Intentions.IDLE.value, 
        {"sprite": mock_crate_state }
    )
    assert result is None


@pytest.mark.workflow_intentions
@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_evaluation_with_environ_functions(
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
        name = "test-goal",
        layer = mock_sprite_state.layer,
        category = Goals.OBJECT.value,
        position = Position(x=1, y=1)
    )
    mock_sprite_state.position.x = 0
    mock_sprite_state.position.y = 0
    
    result = executor.evaluate(
        Intentions.FIND.value, 
        { "sprite": mock_sprite_state }
    )
    assert result == Intentions.INTERACT.value


@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_executor_evaluation_with_bad_arguments(
    implementation,
    mock_translator,
    mock_configurations_schema
):
    translator = mock_translator(implementation[0])  
    executor = translator.compile(mock_configurations_schema.intentions)

    result = executor.evaluate("unknown", {})
    assert result is None
 

@pytest.mark.parametrize("implementation", [
    (Translators.COMPILER.value, CompilerExecutor),
    (Translators.LAMBDA.value, LambdaExecutor)
])
def test_compiler_evaluation_with_bad_conditions(
    implementation,
    mock_translator,
    mock_configurations_schema
):
    translator = mock_translator(implementation[0])  
    mock_configurations_schema.intentions['bad_syntax']  = [Transition(
        next = "more-bad-syntax",
        conditions = [ 'not thing nor any(this for this in thing)']
    )]
    executor = translator.compile(mock_configurations_schema.intentions)
    
    assert len(executor.transitions["bad_syntax"][0].conditions) == 0