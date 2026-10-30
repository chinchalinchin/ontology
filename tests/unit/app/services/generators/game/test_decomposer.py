"""
@domain.test
@test.fixture
@app.services
@workflow.compositions

# Ontology: Tests - tests.unit.services.generators.game.test_decomposer

Unit tests for the Decomposer service.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Orientations
)
from app.models.state import (
    CraftState,
    PropertyState
)
from app.models.config import (
    CompositionConfiguration, 
    CompositionPseudoState
)
from app.models.state import (
    StateSchema, 
    ObjectStateInstances, 
    CraftStateInstances, 
    DoorState
)

# Cython Libraries
from libs.core.models import (
    Position,
    Multiple
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_compositions
]

# -----------------------------------------------------

def test_decomposer_spatial_superposition(mock_decomposer):
    deployed = PropertyState(
        id="brick-house",
        position = Position(x=100, y=100)
    )
    
    assets = mock_decomposer.unpack(deployed)
    assert len(assets) == 6
    
    root_strut = next(a for a in assets if a.id == "home")
    door = next(a for a in assets if a.id == "panel")
    branch_strut = next(a for a in assets if a.id == "hallway")
    
    assert root_strut.state.position.x == 100
    assert root_strut.state.position.y == 100
    
    assert door.state.position.x == 132
    assert door.state.position.y == 244
    
    assert door.state.out.x == 42
    assert door.state.out.y == 154
    
    assert branch_strut.state.position.x == 10
    assert branch_strut.state.position.y == 10


def test_decomposer_late_binding(mock_decomposer):
    deployed = PropertyState(
        id="brick-house",
        layer="binded-layer",
        owner="binded-owner",
        position = Position(x=100, y=100)
    )
    
    assets = mock_decomposer.unpack(deployed)

    root_strut = next(a for a in assets if a.id == "home")
    door = next(a for a in assets if a.id == "panel")
    branch_strut = next(a for a in assets if a.id == "hallway")

    assert root_strut.state.layer == "binded-layer"
    assert door.state.outlayer == "house-layer-1"
    assert branch_strut.state.owner == "binded-owner"


def test_decomposer_nomenclature_generation(mock_decomposer):
    deployed_1 = PropertyState(
        id="brick-house",
        layer="binded-layer",
        owner="binded-owner",
        position = Position(x=0, y=0)
    )
    deployed_2 = PropertyState(
        id="brick-house",
        layer="binded-layer",
        owner="binded-owner",
        position = Position(x=300, y=300)
    )
    
    assets_1 = mock_decomposer.unpack(deployed_1)
    assets_2 = mock_decomposer.unpack(deployed_2)
    
    root_1 = next(a for a in assets_1 if a.id == "home")
    root_2 = next(a for a in assets_2 if a.id == "home")
    door_1 = next(a for a in assets_1 if a.id == "panel")
    door_2 = next(a for a in assets_2 if a.id == "panel")
    
    assert root_1.name == "strut-roof-1-0"
    assert root_2.name == "strut-roof-2-0"
    
    assert door_1.name == "door-strut-roof-1-door-1"
    assert door_2.name == "door-strut-roof-2-door-2"


def test_decomposer_unmapped_composition(mock_decomposer):
    """
    Ensure non-existent composition keys yield empty lists without throwing exceptions.
    """
    deployed = PropertyState(
        id="missing-comp", 
        name="none", 
        layer="0", 
        position=Position(0, 0)
    )
    assert mock_decomposer.unpack(deployed) == []


def test_decomposer_cross_layer_origin_decoupling(mock_decomposer):
    """
    Verify branches on foreign layers decouple from parent layer coordinates and bind to (0, 0).
    """
    deployed = PropertyState(
        id="brick-house",
        layer="binded-layer",
        owner="binded-owner",
        position = Position(x=150, y=750)
    )

    assets = mock_decomposer.unpack(deployed)
    root_strut = next(a for a in assets if a.id == "home")
    interior_wall = next(a for a in assets if a.id == "hallway")
    interior_floor = next(a for a in assets if a.id == "carpet")

    # Root strut reflects deployed position on Layer 0
    assert root_strut.state.layer == "binded-layer"
    assert root_strut.state.position.x == 150
    assert root_strut.state.position.y == 750

    # Branch strut transitions to independent layer; position anchors to layer origin
    assert interior_wall.state.layer == "house-layer-1"
    assert interior_wall.state.position.x == 10
    assert interior_wall.state.position.y == 10

    # Branch component offsets relative to local branch strut origin
    assert interior_floor.state.layer == "house-layer-1"
    assert interior_floor.state.position.x == 10
    assert interior_floor.state.position.y == 106


def test_decomposer_bridge_horizontal_expansion(mock_decomposer, mock_state):
    """
    Verify Decomposer expands horizontal bridge multiplier into discrete unit assets
    with sequential names, offset coordinates, and preserved craft properties.
    """
    state = mock_state(
        AssetCategories.CRAFTS.value,
        AssetInstances.BRIDGES.value,
        position=Position(x=100, y=50),
        blueprint=Orientations.HORIZONTAL.value,
        multiple=Multiple(nx=3, ny=1)
    )

    units = mock_decomposer.multiply(
        state, 
        AssetCategories.CRAFTS.value,
        AssetInstances.BRIDGES.value
    )
    assert len(units) == 3

    assert units[0].name == "test-horizontal-bridge-0"
    assert units[0].state.position.x == 100 + 0 * 80
    assert units[0].state.position.y == 50
    assert units[0].elevation == 0
    assert units[0].substrate == -1

    assert units[1].name == "test-horizontal-bridge-1"
    assert units[1].state.position.x == 100 + 1 * 80
    assert units[1].state.position.y == 50
    assert units[1].elevation == 0
    assert units[1].substrate == -1

    assert units[2].name == "test-horizontal-bridge-2"
    assert units[2].state.position.x == 100 + 2 * 80
    assert units[2].state.position.y == 50
    assert units[2].elevation == 0
    assert units[2].substrate == -1


def test_decomposer_bridge_vertical_expansion(mock_decomposer, mock_state):
    """
    Verify Decomposer expands vertical bridge multiplier along +Y axis.
    """
    state = mock_state(
        AssetCategories.CRAFTS.value,
        AssetInstances.BRIDGES.value,
        position=Position(x=50, y=100),
        blueprint=Orientations.VERTICAL.value,
        multiple=Multiple(nx=1, ny=4)
    )

    units = mock_decomposer.multiply(
        state,
        AssetCategories.CRAFTS.value,
        AssetInstances.BRIDGES.value
    )
    assert len(units) == 4

    assert units[0].state.position.x == 50
    assert units[0].state.position.y == 100
    assert units[1].state.position.x == 50
    assert units[1].state.position.y == 100 + 103
    assert units[2].state.position.x == 50
    assert units[2].state.position.y == 100 + 2 * 103
    assert units[3].state.position.x == 50
    assert units[3].state.position.y == 100 + 3 * 103 


@pytest.mark.app_services
@pytest.mark.workflow_compositions
def test_decomposer_multi_deployment_layer_namespacing(mock_decomposer):
    """
    Verify multi-deployment of identical compositions generates isolated, namespaced
    pseudo-layers across instances (Bug B012 regression prevention).
    """
    deployed1 = PropertyState(
        id="brick-house",
        name="suburbs-00",
        layer="0",
        position=Position(x=100, y=100)
    )
    deployed2 = PropertyState(
        id="brick-house",
        name="suburbs-01",
        layer="0",
        position=Position(x=300, y=100)
    )

    assets1 = mock_decomposer.unpack(deployed1)
    assets2 = mock_decomposer.unpack(deployed2)

    door1_entrance = next(a for a in assets1 if a.id == "panel")
    door2_entrance = next(a for a in assets2 if a.id == "panel")
    interior1_wall = next(a for a in assets1 if a.id == "hallway")
    interior2_wall = next(a for a in assets2 if a.id == "hallway")

    # Each deployment isolates its internal pseudo-layer using the instance increment
    assert door1_entrance.state.outlayer == "house-layer-1"
    assert door2_entrance.state.outlayer == "house-layer-2"

    assert interior1_wall.state.layer == "house-layer-1"
    assert interior2_wall.state.layer == "house-layer-2"