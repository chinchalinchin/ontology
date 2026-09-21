"""
# Ontology: tests.unit.test_app_services_generators__decomposer
"""
# Application Libraries
from app.models.state import PropertyState

# Cython Libraries
from libs.core.models import Position


def test_decomposer_cost_aggregation(mock_decomposer):
    costs = mock_decomposer.cost("test-house")
    cost_dict = {c.item: c.quantity for c in costs}
    
    assert cost_dict.get("wood") == 10
    assert cost_dict.get("stone") == 5

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

def test_decomposer_nomenclature_generation(mock_decomposer):
    deployed1 = PropertyState(id="test-house", name="home", layer="0", position=Position(0,0))
    deployed2 = PropertyState(id="test-house", name="home", layer="0", position=Position(0,0))
    
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

def test_decomposer_unmapped_composition(mock_decomposer):
    """
    Ensure non-existent composition keys yield empty lists without throwing exceptions.
    """
    deployed = PropertyState(id="missing-comp", name="none", layer="0", position=Position(0, 0))
    assert mock_decomposer.unpack(deployed) == []
    assert mock_decomposer.cost("missing-comp") == []

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

def test_decomposer_cross_layer_origin_decoupling(mock_cross_layer_decomposer):
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

    assets = mock_cross_layer_decomposer.unpack(deployed)
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


def test_decomposer_cross_layer_door_out_resolution(mock_cross_layer_decomposer):
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

    assets = mock_cross_layer_decomposer.unpack(deployed)
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