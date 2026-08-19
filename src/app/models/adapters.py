"""
# Ontology: app.models.adapters

Pydantic adapters for instantiating Cython structs across the GIL during YAML parsing.
"""
# Standard Libraries
from typing import Annotated, Any

# External Libraries
from pydantic import BeforeValidator

# Application Libraries
from libs.core.models import Position, Dimensions, Hitbox, Multiple, Velocity

def parse_pos(v: Any) -> Position:
    return Position(**v) if isinstance(v, dict) else v

def parse_dim(v: Any) -> Dimensions:
    return Dimensions(**v) if isinstance(v, dict) else v

def parse_mul(v: Any) -> Multiple:
    return Multiple(**v) if isinstance(v, dict) else v

def parse_vel(v: Any) -> Velocity:
    return Velocity(**v) if isinstance(v, dict) else v

def parse_hb(v: Any) -> Hitbox:
    if isinstance(v, dict):
        return Hitbox(
            position=parse_pos(v.get('position', {})), 
            dimensions=parse_dim(v.get('dimensions', {}))
        )
    return v

PydanticPosition = Annotated[Position, BeforeValidator(parse_pos)]
PydanticDimensions = Annotated[Dimensions, BeforeValidator(parse_dim)]
PydanticMultiple = Annotated[Multiple, BeforeValidator(parse_mul)]
PydanticVelocity = Annotated[Velocity, BeforeValidator(parse_vel)]
PydanticHitbox = Annotated[Hitbox, BeforeValidator(parse_hb)]