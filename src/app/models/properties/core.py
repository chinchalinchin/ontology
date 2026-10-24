"""
@workflow.asset
@workflows.models

# Ontology: app.models.properties.core

Module for typing core property attributes.
"""
from typing import (
    Dict,
    Optional
)
from dataclasses import dataclass

# Applicaiton Libraries
from app.config.enums import (
    Directions,
    Frequencies,
    Materials,
    Organics,
    Ceramics
)
from app.models.adapters import (
    PydanticDimensions as Dimensions, 
)

# --------------------------------------------------------------

@dataclass(slots=True)
class Direction:
    row: int

@dataclass(slots=True)
class Action:
    count: int
    directions: Dict[Directions, Direction]
    delay: int = 1

@dataclass(slots=True)
class Frequency:
    type: Frequencies = Frequencies.CONTINUOUS.value
    delay: int = 1
    frequency: int = 0
    cooldown: int = 60
    persist: bool = False

@dataclass(slots=True)
class Material:
    genus: str
    host: Optional[str] = None

    def __post_init__(self):
        if self.genus == Materials.CHROMATICS.value:
            valid_hosts = (*Organics, *Ceramics)
            if self.host not in valid_hosts:
                raise ValueError(
                    f"Chromatic material requires an organic or ceramic host; got '{self.host}'."
                )
        elif self.host is not None:
            raise ValueError(
                f"Non-chromatic genus '{self.genus}' cannot declare a host material."
            )
            
# --------------------------------------------------------------

@dataclass(slots=True)
class AssetProperties:
    dimensions: Dimensions # type: ignore
    priority: int = 0