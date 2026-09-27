"""
# Ontology: tests.unit.conftest
"""
# Standard Libraries
from unittest.mock import (
    MagicMock, 
    patch
)

# External Libraries
import pytest

# Application Libraries
from app.services.orchestration import (
    Builder, 
    Orchestrator
)
from app.services.generators.menus import (
    Provider,
    Binder
)
from app.services.generators.game import (
    Decomposer,
    Cradle,
    Actuator
)

# ---------------------------------------------------------------------------
# ------------------------------------------------------------- MOCK SERVICES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_decomposer(
    mock_composition_configuration, 
    mock_recipes_configuration,
    mock_properties,
) -> Decomposer:
    # 1. Setup mock properties with costs for aggregation
    return Decomposer(
        compositions=mock_composition_configuration, 
        properties=mock_properties,
        recipes=mock_recipes_configuration
    )


@pytest.fixture
def mock_binder(mock_registry) -> Binder:
    return Binder(
        registry=mock_registry, 
        library=MagicMock()
    )


@pytest.fixture
def mock_builder(
    mock_properties, 
    mock_configurations, 
    mock_state
):
    with patch('app.services.orchestration.builder.Loader') as mock_loader:
        mock_loader.load_properties.return_value = mock_properties
        mock_loader.load_configurations.return_value = mock_configurations
        mock_loader.load_state.return_value = mock_state
        
        yield Builder()


@pytest.fixture
def mock_orchestrator(mock_builder) -> Orchestrator:
    return Orchestrator(mock_builder)


@pytest.fixture
def mock_provider(
    mock_binder, 
    mock_recipes_configuration, 
    mock_widget_properties
) -> Provider:
    return Provider(
        recipes=mock_recipes_configuration.widgets, 
        properties=mock_widget_properties, 
        binder=mock_binder
    )


@pytest.fixture
def mock_cradle(
    mock_decomposer,
    mock_recipes_configuration,
    mock_spawnables
):
    return Cradle(mock_spawnables, mock_recipes_configuration, mock_decomposer)


@pytest.fixture
def mock_actuator(
    mock_shoreline_index
) -> Actuator:
    return Actuator(shorelines=mock_shoreline_index)

