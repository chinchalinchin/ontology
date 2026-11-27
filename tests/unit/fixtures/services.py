"""
@domain.test
@test.fixtures

# Ontology: Test - tests.unit.fixtures.services

Application service, generator, translator, and orchestration fixtures.
"""
# Standard Libraries
from typing import Any, Optional

# External Libraries
import pytest

# Application Libraries
import app.static.settings as settings

from app.game.logic.modules.cognition import (
    CombatInstinct,
    ExploreInstinct,
    GoalResolver,
    Perception,
    Recall,
    SocialInstinct,
    SurvivalInstinct,
)
from app.game.logic.modules.cognition.goals.locators import LocatorOperator
from app.game.logic.modules.cognition.goals.outcomes import OutcomeOperator
from app.game.logic.modules.cognition.goals.reflexes import ReflexOperator
from app.game.logic.modules.cognition.goals.responses import ResponseOperator
from app.game.board import Board
from app.game.logic.relations import MaterialIndex
from app.models.configurations import ConfigurationSchema
from app.models.groups import SpawnableGroup
from app.models.properties import PropertiesSchema
from app.models.state import StateSchema
from app.services.factories import MechanicFactory
from app.services.generators.game import (
    Actuator,
    Cradle,
    Decomposer,
    Perimeter,
)
from app.services.generators.menus import (
    Binder,
    Fabricator,
    Library,
    Provider,
)
from app.services.markets import Materializer
from app.services.orchestration import (
    Builder,
    Migrator,
    Orchestrator,
)
from app.static.semantics import (
    Executors,
    Lifespans,
)

# Cython Libraries
from libs.graphics.registry import Registry

# ---------------------------------------------------------------------------
# ------------------------------------------------- TRANSLATORS & EXECUTORS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_backend():
    """
    Parameterized fixture factory for instantiating an ISL translator ('lambda' or 'compiler').
    """
    def _backend(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ):
        return MechanicFactory.backend(implementation)

    return _backend

@pytest.fixture
def mock_transitions():
    """
    """
    def _transitions(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION
    ):
        return MechanicFactory.transitions(implementation)

    return _transitions

@pytest.fixture
def mock_goals():
    """
    """
    def _goals(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION
    ):
        return MechanicFactory.goals(implementation)

    return _goals

@pytest.fixture
def mock_executors(
    mock_configurations_schema: ConfigurationSchema,
    mock_transitions,
    mock_goals
):
    """
    Parameterized fixture factory compiling intention, plot, and stage executors.
    """
    def _executors(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> dict[str, Any]:
        trans = mock_transitions(implementation)
        goals = mock_goals(implementation)

        compiled: dict[str, Any] = {
            Executors.INTENTION.value: trans.compile(
                mock_configurations_schema.intentions
            ),
            Executors.GOAL.value: goals.compile(
                mock_configurations_schema.goals
            ),
            Executors.PLOT.value: trans.compile(
                mock_configurations_schema.plots
            ),
        }
        if mock_configurations_schema.stages:
            for lifespan in Lifespans:
                stage_rules = mock_configurations_schema.stages.get(
                    lifespan.value
                )
                if stage_rules:
                    compiled[lifespan.value] = trans.compile(stage_rules)
        return compiled

    return _executors

# ---------------------------------------------------------------------------
# --------------------------------------------------------- COGNITION MODULES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_response_operator() -> ResponseOperator:
    return ResponseOperator()


@pytest.fixture
def mock_reflex_operator() -> ReflexOperator:
    return ReflexOperator()


@pytest.fixture
def mock_locator_operator() -> LocatorOperator:
    return LocatorOperator()


@pytest.fixture
def mock_outcome_operator() -> OutcomeOperator:
    return OutcomeOperator()


@pytest.fixture
def mock_goal_resolver(
    mock_configurations_schema: ConfigurationSchema,
    mock_goals,
    mock_response_operator: ResponseOperator,
    mock_reflex_operator: ReflexOperator,
    mock_outcome_operator: OutcomeOperator,
    mock_locator_operator: LocatorOperator,
):
    """
    Parameterized fixture factory building a GoalResolver for a chosen ISL
    backend ('compiler' or 'lambda').
    """
    def _resolver(
        implementation: str = settings.TRANSLATOR_IMPLEMENTATION,
    ) -> GoalResolver:
        evaluator = mock_goals(implementation).compile(
            mock_configurations_schema.goals
        )
        return GoalResolver(
            evaluator=evaluator,
            responses=mock_response_operator,
            reflexes=mock_reflex_operator,
            outcomes=mock_outcome_operator,
            locators=mock_locator_operator,
        )

    return _resolver


@pytest.fixture
def mock_perception() -> Perception:
    return Perception()


@pytest.fixture
def mock_recall() -> Recall:
    return Recall()


@pytest.fixture
def mock_survival_instinct() -> SurvivalInstinct:
    return SurvivalInstinct()


@pytest.fixture
def mock_combat_instinct() -> CombatInstinct:
    return CombatInstinct()


@pytest.fixture
def mock_social_instinct() -> SocialInstinct:
    return SocialInstinct()


@pytest.fixture
def mock_explore_instinct() -> ExploreInstinct:
    return ExploreInstinct()

# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MARKET SERVICES
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_materializer(
    mock_material_index: MaterialIndex,
) -> Materializer:
    """
    Materializer service hydrated with the compiled MaterialIndex.
    """
    return Materializer(materials=mock_material_index)


# ---------------------------------------------------------------------------
# --------------------------------------------------------- GAME GENERATORS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_decomposer(
    mock_configurations_schema: ConfigurationSchema,
    mock_properties_schema: PropertiesSchema,
    mock_material_index: MaterialIndex,
) -> Decomposer:
    """
    Decomposer service configured with compositions, properties, recipes, and materials.
    """
    return Decomposer(
        compositions=mock_configurations_schema.compositions,
        properties=mock_properties_schema,
        recipes=mock_configurations_schema.recipes,
        materials=mock_material_index,
    )


@pytest.fixture
def mock_cradle(
    mock_spawnables: SpawnableGroup,
    mock_configurations_schema: ConfigurationSchema,
    mock_material_index: MaterialIndex,
    mock_decomposer: Decomposer,
) -> Cradle:
    """
    Cradle runtime asset generator injected with spawnables, recipes, materials, and decomposer.
    """
    return Cradle(
        spawnables=mock_spawnables,
        recipes=mock_configurations_schema.recipes,
        materials=mock_material_index,
        decomposer=mock_decomposer,
    )


@pytest.fixture
def mock_actuator() -> Actuator:
    """
    Procedural geography Actuator service.
    """
    return Actuator()


@pytest.fixture
def mock_perimeter() -> Perimeter:
    """
    Boundary contour Perimeter generator service.
    """
    return Perimeter()


# ---------------------------------------------------------------------------
# --------------------------------------------------------- MENU GENERATORS
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_library(
    mock_configurations_schema: ConfigurationSchema,
) -> Library:
    """
    Dialogue and narrative Library service hydrated from configuration.
    """
    return Library(mock_configurations_schema.library)


@pytest.fixture
def mock_binder(
    mock_registry: Registry,
    mock_library: Library,
) -> Binder:
    """
    Widget state Binder wired to concrete Registry and Library instances.
    """
    return Binder(
        registry=mock_registry,
        library=mock_library,
    )


@pytest.fixture
def mock_fabricator() -> Fabricator:
    """
    Menu layout Fabricator service.
    """
    return Fabricator()


@pytest.fixture
def mock_provider(
    mock_configurations_schema: ConfigurationSchema,
    mock_properties_schema: PropertiesSchema,
    mock_binder: Binder,
    mock_fabricator: Fabricator,
) -> Provider:
    """
    Menu Provider service wired with widget recipes, widget properties, Binder, and Fabricator.
    """
    return Provider(
        mock_configurations_schema.recipes.widgets,
        mock_properties_schema.widgets,
        mock_binder,
        mock_fabricator,
    )


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- ORCHESTRATION
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_migrator(
    mock_board: Board,
    mock_properties_schema: PropertiesSchema,
    mock_configurations_schema: ConfigurationSchema,
    mock_decomposer: Decomposer,
    mock_material_index: MaterialIndex,
):
    """
    Fixture factory constructing a Migrator bound to a target Board.
    """
    def _migrator(target_board: Optional[Board] = None) -> Migrator:
        active_board = target_board or mock_board
        instance = Migrator(
            board=active_board,
            properties=mock_properties_schema,
            configurations=mock_configurations_schema,
            decomposer=mock_decomposer,
            materials=mock_material_index,
        )
        active_board.set_migrator(instance)
        return instance

    return _migrator()


@pytest.fixture
def mock_builder(
    monkeypatch,
    testbed: str,
    mock_state_schema: StateSchema,
) -> Builder:
    """
    Concrete Builder instance with state loading routed to the testbed schema.
    """
    monkeypatch.setattr(
        "app.static.loader.Loader.load_state",
        lambda state=testbed: mock_state_schema,
    )
    monkeypatch.setattr("app.static.settings.NEW_BOARD", testbed)
    return Builder()


@pytest.fixture
def mock_orchestrator(mock_builder: Builder) -> Orchestrator:
    """
    Concrete Orchestrator initialized with mock_builder.
    """
    return Orchestrator(mock_builder)