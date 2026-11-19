"""
@domain.concrete
@app.asset
@app.core
@asset.frame
@category.cursors

# Ontology: Source - app.assets.frames.cursors

Cursor Frame implementations.
"""
# Standard Libraries
from typing import (
    Dict,
    List,
    Tuple
)
import logging

# Application Libraries
import app.static.settings as settings
from app.assets.base import Frame
from app.models.properties import CursorProperties
from app.models.state import MotorState

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------


class ProjectileFrame(Frame):
    """
    Frame strategy for load-time rotated projectile texture strips.
    Indexes discrete angular cells k * properties.rotation along a single horizontal row
    and resolves active keys directly from MotorState.angle.
    """

    def keys(self, id: str, state: MotorState) -> List[Tuple[str, int, int]]:
        """
        Projects MotorState.angle directly to its pre-rotated Registry frame key.
        """
        angle = (state.angle % 360) if state is not None else 0
        frame_key = settings.SEPARATOR.join([
            id,
            str(angle)
        ])
        return [(frame_key, 0, 0)]

    def index(
        self,
        id: str,
        properties: CursorProperties
    ) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Generates crop mappings (k * w, 0, w, l) for every discrete angle
        k * properties.rotation in [0, 360).
        """
        rotation = properties.rotation if properties.rotation is not None else 90
        if rotation <= 0 or rotation > 360 or (360 % rotation) != 0:
            raise ValueError(
                f"Invalid projectile rotation step for '{id}': {rotation}"
            )

        w = properties.dimensions.w
        l = properties.dimensions.l
        count = 360 // rotation
        crops: Dict[str, Tuple[int, int, int, int]] = {}

        for k in range(count):
            angle = k * rotation
            frame_key = settings.SEPARATOR.join([
                id,
                str(angle)
            ])
            crops[frame_key] = (k * w, 0, w, l)

        return crops