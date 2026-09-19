"""
# Ontology: app.models.adapters

Pydantic adapters for instantiating Cython structs across the GIL during YAML parsing.
"""
from typing import Annotated, Any, TYPE_CHECKING
from pydantic import PlainValidator, PlainSerializer  # type: ignore

from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox, 
    Multiple, 
    Velocity, 
    ScreenPosition
)

# ---------------------------------------------------------------------------
# --------------------------------------------------------------- DESERIALIZE

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

# ---------------------------------------------------------------------------
# ----------------------------------------------------------------- SERIALIZE

def serialize_pos(v: Any) -> Any:
    if v is None or isinstance(v, dict):
        return v
    return {"x": v.x, "y": v.y}

def serialize_dim(v: Any) -> Any:
    if v is None or isinstance(v, dict):
        return v
    return {"w": v.w, "l": v.l}

def serialize_mul(v: Any) -> Any:
    if v is None or isinstance(v, dict):
        return v
    return {"nx": v.nx, "ny": v.ny}

def serialize_vel(v: Any) -> Any:
    if v is None or isinstance(v, dict):
        return v
    return {"vx": v.vx, "vy": v.vy}

def serialize_hb(v: Any) -> Any:
    if v is None or isinstance(v, dict):
        return v
    pos = getattr(v, "position", None)
    dim = getattr(v, "dimensions", None) or getattr(v, "dimension", None)
    return {
        "position": serialize_pos(pos),
        "dimensions": serialize_dim(dim)
    }

def serialize_sp(v: Any) -> Any:
    if v is None or isinstance(v, dict):
        return v
    return {"px": v.px, "py": v.py}

# ---------------------------------------------------------------------------
# ------------------------------------------------------------------- EXPORTS

# 1. Provide strict C-types to static analyzers and IDEs
if TYPE_CHECKING:
    PydanticPosition = Position
    PydanticDimensions = Dimensions
    PydanticMultiple = Multiple
    PydanticVelocity = Velocity
    PydanticHitbox = Hitbox
    PydanticScreenPosition = ScreenPosition
# 2. Provide bidirectional validation/serialization to Pydantic at runtime
else:
    PydanticPosition = Annotated[
        Any, 
        PlainValidator(parse_pos), 
        PlainSerializer(serialize_pos, when_used="unless-none")
    ]
    PydanticDimensions = Annotated[
        Any, 
        PlainValidator(parse_dim), 
        PlainSerializer(serialize_dim, when_used="unless-none")
    ]
    PydanticMultiple = Annotated[
        Any, 
        PlainValidator(parse_mul), 
        PlainSerializer(serialize_mul, when_used="unless-none")
    ]
    PydanticVelocity = Annotated[
        Any, 
        PlainValidator(parse_vel), 
        PlainSerializer(serialize_vel, when_used="unless-none")
    ]
    PydanticHitbox = Annotated[
        Any, 
        PlainValidator(parse_hb), 
        PlainSerializer(serialize_hb, when_used="unless-none")
    ]
    PydanticScreenPosition = Annotated[
        Any, 
        PlainValidator(parse_sp), 
        PlainSerializer(serialize_sp, when_used="unless-none")
    ]