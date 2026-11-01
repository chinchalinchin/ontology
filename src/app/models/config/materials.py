
"""
@app.config
@workflow.compositions

# Ontology: Source - app.models.config.materials

Material Configuration Models.
"""

# Standard Libraries
from typing import (
    Dict,
    Union,
    Optional
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Blueprints,
    Materials,
    Organics,
    Chromatics,
    Ceramics,
    Metallics,
    Geologics,
    MultiplicationStrategies,
    Buildings,
    Corridors,
    Columns,
    Decor,
    Enclosures,
    Orientations,
    Inclines,
    Directions,
    Substrates
)
from app.models.adapters import Enumerated
from app.models.config.core import Configuration

# ---------------------------------------------------------

@dataclass(slots=True)
class Cost:
    item: str
    quantity: int

@dataclass(slots=True, frozen=True)
class MaterialSpace:
    host: Optional[Enumerated[Materials]] = None
    partitions: Dict[Union[
        Enumerated[Organics], 
        Enumerated[Chromatics], 
        Enumerated[Ceramics], 
        Enumerated[Metallics],
        Enumerated[Geologics]
    ], float] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class BlueprintPartition:
    delta: float = 1.0
    substrate: Enumerated[Substrates] = Substrates.STANDARD.value
    obstacle: bool = False

@dataclass(slots=True, frozen=True)
class BlueprintSpace:
    strategy: MultiplicationStrategies = MultiplicationStrategies.SIMPLE.value
    partitions: Dict[Union[
        Enumerated[Buildings],
        Enumerated[Corridors],
        Enumerated[Columns],
        Enumerated[Enclosures],
        Enumerated[Orientations],
        Enumerated[Directions],
        Enumerated[Decor],
        Enumerated[Inclines]
    ], BlueprintPartition] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class MaterialsConfiguration(Configuration):
    genera: Dict[
        Enumerated[Materials], 
        MaterialSpace
    ] = field(default_factory=dict)
    blueprints: Dict[
        Enumerated[Blueprints], 
        BlueprintSpace
    ] = field(default_factory=dict)
    substrates: Dict[
        Enumerated[AssetInstances], 
        Substrates
    ] = field(default_factory=dict)