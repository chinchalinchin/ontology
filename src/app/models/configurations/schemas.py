"""
@domain.model
@app.config
@app.schema

# Ontology: Source - app.models.configurations.schemas

Models for typing Configuration schemas.
"""
# Standard Libraries
from typing import (
    Dict, 
    List, 
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.static.semantics import (
    Intentions,
    Goals,
    Outcomes
)
from app.models.adapters import Enumerated
from app.models.configurations.assets import (
    ActionConfiguration,
    CompositionConfiguration,
    MaterialsConfiguration,
    RecipeConfiguration
)
from app.models.configurations.automata import (
    IntentionConfiguration,
    PlotConfiguration,
    StageConfiguration,
    GoalConfiguration
)
from app.models.configurations.engine import (
    MechanicsConfiguration,
    MappingConfiguration
)
from app.models.configurations.menus import (
    MenuConfiguration
)
# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ConfigurationSchema:
    actions: List[ActionConfiguration] = field(default_factory=list)
    compositions: Dict[str, CompositionConfiguration] = field(default_factory=dict)
    intentions: Dict[Enumerated[Intentions], List[IntentionConfiguration]] = field(default_factory=dict)
    library: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    mappings: MappingConfiguration = field(default_factory=MappingConfiguration)
    materials: MaterialsConfiguration = field(default_factory=MaterialsConfiguration)
    mechanics: MechanicsConfiguration = field(default_factory=MechanicsConfiguration)
    plots: Dict[str, List[PlotConfiguration]] = field(default_factory=dict)
    stages: Dict[str, Dict[str, List[StageConfiguration]]] = field(default_factory=dict)
    recipes: RecipeConfiguration = field(default_factory=RecipeConfiguration)
    menus: Dict[str, MenuConfiguration] = field(default_factory=dict)
    goals: Dict[Enumerated[Goals], Dict[Enumerated[Outcomes], GoalConfiguration]]