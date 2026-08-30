"""
# Ontology: tests.unit.test_app_services_generators__decomposer
"""
import pytest
from app.services.generators.decomposer import Decomposer
from app.models.config import CompositionConfiguration, CompositionPseudoState, RecipeConfiguration
from app.models.properties import PropertiesSchema, CraftProperties, Cost
from app.models.state import PropertyState, StateSchema, ObjectStateInstances, DoorState
from libs.core.models import Position, Dimensions

@pytest.fixture
def mock_decomposer():
    # 1. Setup mock properties with costs for aggregation
    props = PropertiesSchema()
    props.crafts.struts["frame-wood"] = CraftProperties(
        dimensions=Dimensions(w=100, l=100),
        cost=[Cost(item="wood", quantity=10)]
    )
    props.crafts.struts["wall-blue"] = CraftProperties(
        dimensions=Dimensions(w=50, l=50),
        cost=[Cost(item="stone", quantity=5)]
    )

    # 2. Setup a complex Composition with a root, a branch, and a component
    comp_config = CompositionConfiguration(
        root=CompositionPseudoState(
            strut=PropertyState(id="frame-wood", name="base_house"),
            components=StateSchema(
                objects=ObjectStateInstances(
                    doors=[
                        DoorState(
                            id="door-front",
                            name="entrance",
                            position=Position(x=20, y=20),
                            out=Position(x=5, y=5),
                            outlayer="bind(root.layer)"
                        )
                    ]
                )
            )
        ),
        branches=[
            CompositionPseudoState(
                strut=PropertyState(
                    id="wall-blue", 
                    name="interior",
                    position=Position(x=10, y=10),
                    owner="bind(parent.owner)"
                ),
                components=StateSchema()
            )
        ]
    )
    
    compositions = {"test-house": comp_config}
    recipes = RecipeConfiguration()
    
    return Decomposer(compositions=compositions, properties=props, recipes=recipes)

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