"""
@domain.concrete
@app.asset
@category.cursors
@asset.hitbox

# Ontology: Source - app.assets.hitboxes.cursors

Cursor HitboxSchema implementations.
"""
# Standard Libraries
import math
from typing import List

# Application Libraries
from app.assets.base import HitboxSchema
from app.models.properties import CursorProperties
from app.models.state import MotorState

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Hitbox,
    Position
)

# ---------------------------------------------------------


class RotatedHitbox(HitboxSchema):
    """
    Projects canonical 0-degree CursorProperties hitboxes clockwise around
    the frame center (W / 2, L / 2) by MotorState.angle into tight AABBs.
    """

    def elevations(
        self,
        properties: CursorProperties,
        state: MotorState
    ) -> List[int]:
        """
        Returns the discrete elevation plane occupied by the projectile.
        """
        return [max(0, state.elevation if state.elevation is not None else 0)]

    def get(
        self,
        properties: CursorProperties,
        state: MotorState,
        elevation: int
    ) -> List[Hitbox]:
        """
        Computes rotated AABB hitboxes at the requested elevation plane.
        Falls back to the full frame dimensions when properties.hitboxes is None.
        """
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if not properties.dimensions:
            return []

        base_hitboxes = properties.hitboxes
        if base_hitboxes is None:
            base_hitboxes = [Hitbox(Position(0, 0), properties.dimensions)]
        elif not base_hitboxes:
            return []

        angle = state.angle % 360
        if angle == 0:
            cos_t, sin_t = 1.0, 0.0
        elif angle == 90:
            cos_t, sin_t = 0.0, 1.0
        elif angle == 180:
            cos_t, sin_t = -1.0, 0.0
        elif angle == 270:
            cos_t, sin_t = 0.0, -1.0
        else:
            rad = math.radians(angle)
            cos_t = math.cos(rad)
            sin_t = math.sin(rad)

        abs_cos = abs(cos_t)
        abs_sin = abs(sin_t)
        cx = properties.dimensions.w / 2.0
        cy = properties.dimensions.l / 2.0

        rotated: List[Hitbox] = []
        for hb in base_hitboxes:
            w0 = hb.dimensions.w
            l0 = hb.dimensions.l

            h_cx = (hb.position.x + (w0 / 2.0)) - cx
            h_cy = (hb.position.y + (l0 / 2.0)) - cy

            rot_cx = (cos_t * h_cx) - (sin_t * h_cy)
            rot_cy = (sin_t * h_cx) + (cos_t * h_cy)

            rot_w = max(1, round((w0 * abs_cos) + (l0 * abs_sin)))
            rot_l = max(1, round((w0 * abs_sin) + (l0 * abs_cos)))

            rot_x = round(cx + rot_cx - (rot_w / 2.0))
            rot_y = round(cy + rot_cy - (rot_l / 2.0))

            rotated.append(Hitbox(Position(rot_x, rot_y), Dimensions(rot_w, rot_l)))

        return rotated