"""
# Ontology: app.models.adapters

Pydantic adapters for instantiating Cython structs across the GIL during YAML parsing.
"""
from typing import Annotated, Any, TYPE_CHECKING
from pydantic import PlainValidator # type: ignore

from libs.core.models import Position, Dimensions, Hitbox, Multiple, Velocity, ScreenPosition

def parse_pos(v: Any) -> Any:
    return Position(**v) if isinstance(v, dict) else v

def parse_dim(v: Any) -> Any:
    return Dimensions(**v) if isinstance(v, dict) else v

def parse_mul(v: Any) -> Any:
    return Multiple(**v) if isinstance(v, dict) else v

def parse_vel(v: Any) -> Any:
    return Velocity(**v) if isinstance(v, dict) else v

def parse_hb(v: Any) -> Any:
    if isinstance(v, dict):
        return Hitbox(
            position=parse_pos(v.get('position', {})), 
            dimensions=parse_dim(v.get('dimensions', {}))
        )
    return v

def parse_sp(v: Any) -> Any:
    return ScreenPosition(**v) if isinstance(v, dict) else v

# 1. Provide strict C-types to static analyzers and IDEs
if TYPE_CHECKING:
    PydanticPosition = Position
    PydanticDimensions = Dimensions
    PydanticMultiple = Multiple
    PydanticVelocity = Velocity
    PydanticHitbox = Hitbox
    PydanticScreenPosition = ScreenPosition
# 2. Provide `Any` to Pydantic at runtime to bypass schema generation crashes
else:
    PydanticPosition = Annotated[Any, PlainValidator(parse_pos)]
    PydanticDimensions = Annotated[Any, PlainValidator(parse_dim)]
    PydanticMultiple = Annotated[Any, PlainValidator(parse_mul)]
    PydanticVelocity = Annotated[Any, PlainValidator(parse_vel)]
    PydanticHitbox = Annotated[Any, PlainValidator(parse_hb)]
    PydanticScreenPosition = Annotated[Any, PlainValidator(parse_sp)]