"""
# Ontology: app.assets.frames.objects

Package for Object Frame implementations.
"""
# Standard Libraries
from typing import (
    List,
    Tuple,
    Dict,
    Union
)
import logging

# Application Libraries
import app.config.settings as settings
from app.assets.base import Frame
from app.config.enums import (
    ChannelTypes,
    LayerProjections
)
from app.models.properties import ObjectProperties
from app.models.state import (
    ObjectState,
    DoorState,
    ContainerState,
    SwitchState
)

logger = logging.getLogger(__name__)


class ObjectFrame(Frame):
    """
    Indexes single-row Material-column Object atlases (Crates, Doors, Signs)
    where columns correspond to Material genus partitions.
    """

    def index(
        self,
        id: str,
        properties: ObjectProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l

        if not properties.material:
            return {id: (0, 0, w, l)}

        cols = settings.MATERIAL_PARTITIONS.get(properties.material.genus, ())
        return {
            settings.SEPARATOR.join([id, mat]): (c_idx * w, 0, w, l)
            for c_idx, mat in enumerate(cols)
        }

    def keys(self, id: str, state: ObjectState) -> List[Tuple[str, int, int]]:
        if not state.material:
            return [(id, 0, 0)]
        key = settings.SEPARATOR.join([id, state.material])
        return [(key, 0, 0)]

    def channels(
        self,
        id: str,
        state: ObjectState,
        properties: ObjectProperties
    ) -> List[Tuple]:
        directives = super().channels(id, state, properties)
        if isinstance(state, DoorState) and state.projection == LayerProjections.OUT.value:
            # Project solid dark alpha footprint on outlayer
            directives.append((
                ChannelTypes.TINT.value,
                (0, 0, 0, 0, 110)
            ))
        return directives


class BinaryFrame(Frame):
    """
    Indexes 2D (Switch_Row x Material_Col) Binary Object atlases (Chests, Gates)
    where rows correspond to binary states (0: closed, 1: open) and columns
    correspond to Material genus partitions.
    """

    def index(
        self,
        id: str,
        properties: ObjectProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l

        if not properties.material:
            return {
                settings.SEPARATOR.join([id, str(r_idx)]): (r_idx * w, 0, w, l)
                for r_idx in range(properties.count)
            }

        cols = settings.MATERIAL_PARTITIONS.get(properties.material.genus, ())
        atlas: Dict[str, Tuple[int, int, int, int]] = {}
        for r_idx in range(properties.count):
            for c_idx, mat in enumerate(cols):
                key = settings.SEPARATOR.join([id, str(r_idx), mat])
                atlas[key] = (c_idx * w, r_idx * l, w, l)
        return atlas

    def keys(
        self,
        id: str,
        state: Union[ContainerState, SwitchState]
    ) -> List[Tuple[str, int, int]]:
        frame_idx = str(state.animation.frame)
        if not state.material:
            return [(settings.SEPARATOR.join([id, frame_idx]), 0, 0)]
        key = settings.SEPARATOR.join([id, frame_idx, state.material])
        return [(key, 0, 0)]