"""
@domain.concrete
@app.asset
@asset.hitbox
@category.objects

# Ontology: Source - app.assets.hitboxes.objects

Object HitboxSchema implementations.
"""
# Standard Libraries
from typing import (
    List,
    Optional
)

# Application Libraries
from app.assets.base import (
    Frame,
    HitboxSchema
)
from app.assets.hitboxes.core import StaticHitbox
from app.static.semantics import LayerProjections
from app.models.properties import ObjectProperties
from app.models.state import (
    DoorState,
    SwitchState
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

# ---------------------------------------------------------

DEFAULT_IN_THRESHOLD_CLEARANCE = 12
DEFAULT_OUT_SENSOR_THICKNESS = 16

# ---------------------------------------------------------


class SwitchHitbox(StaticHitbox):
    """
    Resolves dynamic hitboxes for binary switchable obstacles (Gates).
    Emits [] when state.switch is True (open) and active hitboxes when False (closed).
    """

    def elevations(
        self,
        properties: ObjectProperties,
        state: SwitchState
    ) -> List[int]:
        if state.switch:
            return []
        return super().elevations(properties, state)

    def get(
        self,
        properties: ObjectProperties,
        state: SwitchState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        if state.switch:
            return []
        return super().get(properties, state, elevation, frame)


class LayeredHitbox(HitboxSchema):
    """
    Resolves categorical layer-relative hitboxes for Doors across their deployed
    layer ('in') and connected outlayer shadow footprint ('out').
    """

    def elevations(
        self,
        properties: ObjectProperties,
        state: DoorState
    ) -> List[int]:
        if state.projection == LayerProjections.OUT.value:
            return []
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: ObjectProperties,
        state: DoorState,
        elevation: int,
        frame: Optional[Frame] = None
    ) -> List[Hitbox]:
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        projection = state.projection or LayerProjections.IN.value

        if isinstance(properties.hitboxes, dict):
            return properties.hitboxes.get(projection, []) or []

        if properties.hitboxes is not None and projection == LayerProjections.IN.value:
            return properties.hitboxes

        if not properties.dimensions:
            return []

        w = properties.dimensions.w
        l = properties.dimensions.l

        if projection == LayerProjections.OUT.value:
            return [
                Hitbox(
                    Position(0, 0),
                    Dimensions(w, min(l, DEFAULT_OUT_SENSOR_THICKNESS))
                )
            ]

        return [
            Hitbox(
                Position(0, 0),
                Dimensions(w, max(1, l - DEFAULT_IN_THRESHOLD_CLEARANCE))
            )
        ]
