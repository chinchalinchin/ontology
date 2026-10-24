
"""
# Ontology: app.models.config

Models for typing the Market configuration.
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
    Enclosures,
    Orientations,
    Inclines,
    Directions,
    Substrates
)
from app.models.config.core import Configuration

# ---------------------------------------------------------

@dataclass(slots=True)
class Cost:
    item: str
    quantity: int

@dataclass(slots=True, frozen=True)
class MaterialSpace:
    host: Optional[Materials] = None
    partitions: Dict[Union[
        Organics, 
        Chromatics, 
        Ceramics, 
        Metallics,
        Geologics
    ], float] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class BlueprintPartition:
    delta: float = 1.0
    substrate: Substrates = Substrates.STANDARD.value
    obstacle: bool = False

@dataclass(slots=True, frozen=True)
class BlueprintSpace:
    strategy: MultiplicationStrategies = MultiplicationStrategies.SIMPLE.value
    partitions: Dict[Union[
        Buildings,
        Corridors,
        Columns,
        Enclosures,
        Orientations,
        Directions,
        Inclines
    ], BlueprintPartition] = field(default_factory=dict)

@dataclass(slots=True, frozen=True)
class MaterialsConfiguration(Configuration):
    genera: Dict[Materials, MaterialSpace] = field(default_factory=dict)
    blueprints: Dict[Blueprints, BlueprintSpace] = field(default_factory=dict)
    substrates: Dict[AssetInstances, Substrates] = field(default_factory=dict)