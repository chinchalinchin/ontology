"""
# Ontology: tests.unit.services.generators.test_decomposer
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import Orientations
from app.models.state import (
    BridgeState,
    PropertyState
)

# Cython Libraries
from libs.core.models import (
    Position,
    Multiple
)


@pytest.mark.services
def test_decomposer_cost_aggregation(mock_decomposer):
    costs = mock_decomposer.cost("test-house")
    cost_dict = {c.item: c.quantity for c in costs}
    
    assert cost_dict.get("wood") == 10
    assert cost_dict.get("stone") == 5


@pytest.mark.services
def test_decomposer_spatial_superposition(mock_decomposer):
    deployed = PropertyState(
        id="test-house",
        name="my_house",
        layer="layer_1",
        owner="player",
        position=Position(x=100, y=100)
    )
    
    assets = mock_decomposer.unpack(deployed)
    assert len(assets) == 3
    
    root_strut = next(a for a in assets if a.id == "frame-wood")
    door = next(a for a in assets if a.id == "door-front")
    branch_strut = next(a for a in assets if a.id == "wall-blue")
    
    assert root_strut.state.position.x == 100
    assert root_strut.state.position.y == 100
    
    assert door.state.position.x == 120
    assert door.state.position.y == 120
    
    assert door.state.out.x == 105
    assert door.state.out.y == 105
    
    assert branch_strut.state.position.x == 110
    assert branch_strut.state.position.y == 110


@pytest.mark.services
def test_decomposer_late_binding(mock_decomposer):
    deployed = PropertyState(
        id="test-house",
        name="my_house",
        layer="layer_1",
        owner="player",
        position=Position(x=100, y=100)
    )
    
    assets = mock_decomposer.unpack(deployed)
    door = next(a for a in assets if a.id == "door-front")
    branch_strut = next(a for a in assets if a.id == "wall-blue")
    
    assert door.state.outlayer == "layer_1"
    assert branch_strut.state.owner == "player"


@pytest.mark.services
def test_decomposer_nomenclature_generation(mock_decomposer):
    deployed1 = PropertyState(
        id="test-house",
        name="home", 
        layer="0", 
        position=Position(0,0)
    )
    deployed2 = PropertyState(
        id="test-house",
        name="home", 
        layer="0", 
        position=Position(0,0)
    )
    
    assets1 = mock_decomposer.unpack(deployed1)
    assets2 = mock_decomposer.unpack(deployed2)
    
    root1 = next(a for a in assets1 if a.id == "frame-wood")
    root2 = next(a for a in assets2 if a.id == "frame-wood")
    door1 = next(a for a in assets1 if a.id == "door-front")
    door2 = next(a for a in assets2 if a.id == "door-front")
    
    assert root1.name == "strut-base_house-1"
    assert root2.name == "strut-base_house-2"
    
    # The component appends its instance and the new increment to the fully hydrated parent name
    assert door1.name == "door-strut-base_house-1-1"
    assert door2.name == "door-strut-base_house-2-2"


@pytest.mark.services
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
    assert mock_decomposer.cost("missing-comp") == []


@pytest.mark.services
def test_decomposer_resolve_bind_patterns(mock_decomposer):
    """
    Validate bind parsing logic across explicit parent, explicit root, and legacy syntax.
    """
    root_ctx = {"layer": "world_1", "owner": "alice"}
    parent_ctx = {"layer": "sub_2", "owner": "bob"}
    
    # Non-string values pass through unaltered
    assert mock_decomposer._resolve_bind(100, root_ctx, parent_ctx) == 100
    
    # Unbound strings pass through unaltered
    assert mock_decomposer._resolve_bind("stone_wall", root_ctx, parent_ctx) == "stone_wall"
    
    # Explicit parent binding
    assert mock_decomposer._resolve_bind("bind(parent.owner)", root_ctx, parent_ctx) == "bob"
    
    # Explicit root binding
    assert mock_decomposer._resolve_bind("bind(root.layer)", root_ctx, parent_ctx) == "world_1"
    
    # Legacy prefix-free root binding
    assert mock_decomposer._resolve_bind("bind(owner)", root_ctx, parent_ctx) == "alice"
    
    # Unmatched keys return the original bind expression
    assert mock_decomposer._resolve_bind("bind(parent.nonexistent)", root_ctx, parent_ctx) == "bind(parent.nonexistent)"


@pytest.mark.services
def test_decomposer_cross_layer_origin_decoupling(mock_decomposer):
    """
    Verify branches on foreign layers decouple from parent layer coordinates and bind to (0, 0).
    """
    deployed = PropertyState(
        id="brick-house",
        name="door-test",
        layer="0",
        owner="player",
        position=Position(x=150, y=750)
    )

    assets = mock_decomposer.unpack(deployed)
    root_strut = next(a for a in assets if a.id == "frame-brick")
    interior_wall = next(a for a in assets if a.id == "wall-blue")
    interior_floor = next(a for a in assets if a.id == "floor-wood")

    # Root strut reflects deployed position on Layer 0
    assert root_strut.state.layer == "0"
    assert root_strut.state.position.x == 150
    assert root_strut.state.position.y == 750

    # Branch strut transitions to independent layer; position anchors to layer origin
    assert interior_wall.state.layer == "brick-house-compose-layer"
    assert interior_wall.state.position.x == 0
    assert interior_wall.state.position.y == 0

    # Branch component offsets relative to local branch strut origin
    assert interior_floor.state.layer == "brick-house-compose-layer"
    assert interior_floor.state.position.x == 0
    assert interior_floor.state.position.y == 96


@pytest.mark.services
def test_decomposer_cross_layer_door_out_resolution(mock_decomposer):
    """
    Ensure entrance doors output to local interior coordinates while exit doors offset by root position.
    """
    deployed = PropertyState(
        id="brick-house",
        name="door-test",
        layer="0",
        owner="player",
        position=Position(x=150, y=750)
    )

    assets = mock_decomposer.unpack(deployed)
    entrance_door = next(a for a in assets if a.id == "door-house")
    exit_door = next(a for a in assets if a.id == "door-shadow")

    # Entrance door: target is foreign interior layer; out coordinate remains local
    assert entrance_door.state.layer == "0"
    assert entrance_door.state.outlayer == "brick-house-compose-layer"
    assert entrance_door.state.out.x == 82
    assert entrance_door.state.out.y == 143

    # Exit door: target matches root context layer; out coordinate offsets by deployed root position
    assert exit_door.state.layer == "brick-house-compose-layer"
    assert exit_door.state.outlayer == "0"
    assert exit_door.state.out.x == 193  # 150 + 43
    assert exit_door.state.out.y == 913  # 750 + 163


@pytest.mark.fluids
@pytest.mark.services
def test_decomposer_bridge_horizontal_expansion(mock_decomposer):
    """
    Verify Decomposer expands horizontal bridge multiplier into discrete unit assets
    with sequential names, offset coordinates, and preserved craft properties.
    """
    state = BridgeState(
        id="wood-bridge",
        name="river-crossing",
        layer="0",
        position=Position(x=100, y=50),
        orientation=Orientations.HORIZONTAL.value,
        multiple=Multiple(nx=3, ny=1)
    )

    units = mock_decomposer.bridge(state)
    assert len(units) == 3

    assert units[0].name == "river-crossing-0"
    assert units[0].state.position.x == 100
    assert units[0].state.position.y == 50
    assert units[0].state.depth == 1
    assert units[0].state.height == 0

    assert units[1].name == "river-crossing-1"
    assert units[1].state.position.x == 132  # 100 + 32
    assert units[1].state.position.y == 50

    assert units[2].name == "river-crossing-2"
    assert units[2].state.position.x == 164  # 100 + 64
    assert units[2].state.position.y == 50


@pytest.mark.fluids
@pytest.mark.services
def test_decomposer_bridge_vertical_expansion(mock_decomposer):
    """
    Verify Decomposer expands vertical bridge multiplier along +Y axis.
    """
    state = BridgeState(
        id="wood-bridge",
        name="chasm-bridge",
        layer="0",
        position=Position(x=50, y=100),
        orientation=Orientations.VERTICAL.value,
        multiple=Multiple(nx=1, ny=2)
    )

    units = mock_decomposer.bridge(state)
    assert len(units) == 2

    assert units[0].state.position.x == 50
    assert units[0].state.position.y == 100
    assert units[1].state.position.x == 50
    assert units[1].state.position.y == 132


@pytest.mark.fluids
@pytest.mark.services
def test_decomposer_bridge_linear_cost(mock_decomposer):
    """
    Verify bridge construction cost scales linearly with span length (N * cost).
    """
    mult = Multiple(nx=4, ny=1)
    costs = mock_decomposer.bridge_cost(
        "wood-bridge",
        mult,
        Orientations.HORIZONTAL.value
    )
    assert len(costs) == 1
    assert costs[0].item == "wood"
    assert costs[0].quantity == 8  # 4 * 2