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
from typing import (
    Dict,
    List,
    Tuple,
)

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

MAX_CACHED_CURSOR_TABLES = 512

# ---------------------------------------------------------


class RotatedHitbox(HitboxSchema):
    """
    Projects canonical 0-degree CursorProperties hitboxes clockwise around
    the frame center (W / 2, L / 2) by MotorState.angle into tight AABBs.
    """
    _angle_tables: Dict[int, Tuple[CursorProperties, Dict[int, List[Hitbox]]]]

    def __init__(self) -> None:
        """Initializes quantized angle lookup tables keyed by CursorProperties identity."""
        if not hasattr(self, "_angle_tables"):
            self._angle_tables = {}

    @staticmethod
    def _rotate(
        base_hitboxes: List[Hitbox],
        w: int,
        l: int,
        angle: int
    ) -> List[Hitbox]:
        """Projects base hitboxes clockwise about frame center (w / 2, l / 2) by angle."""
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
        cx = w / 2.0
        cy = l / 2.0

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

    def precompute(self, properties: CursorProperties) -> Dict[int, List[Hitbox]]:
        """
        Precomputes and caches the quantized angle hitbox table for a CursorProperties instance.
        """
        if not properties.dimensions:
            return {}

        if properties.hitboxes is None:
            base_hitboxes = self._dimension_fallback(properties.dimensions)
        elif not properties.hitboxes:
            return {}
        else:
            base_hitboxes = properties.hitboxes

        w = properties.dimensions.w
        l = properties.dimensions.l
        step = properties.rotation
        table: Dict[int, List[Hitbox]] = {}

        if step and step > 0 and (360 % step) == 0:
            for angle in range(0, 360, step):
                table[angle] = self._rotate(base_hitboxes, w, l, angle)

        if len(self._angle_tables) >= MAX_CACHED_CURSOR_TABLES:
            self._angle_tables.clear()

        self._angle_tables[id(properties)] = (properties, table)
        return table

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
        Retrieves precomputed rotated AABB hitboxes at the requested elevation plane.
        Falls back to the full frame dimensions when properties.hitboxes is None.
        """
        target_e = max(0, state.elevation if state.elevation is not None else 0)
        if max(0, elevation) != target_e:
            return []

        if not properties.dimensions:
            return []

        if properties.hitboxes is not None and not properties.hitboxes:
            return []

        entry = self._angle_tables.get(id(properties))
        if entry is not None and entry[0] is properties:
            table = entry[1]
        else:
            table = self.precompute(properties)

        angle = state.angle % 360
        cached = table.get(angle)
        if cached is not None:
            return cached

        base_hitboxes = (
            self._dimension_fallback(properties.dimensions)
            if properties.hitboxes is None
            else properties.hitboxes
        )
        rotated = self._rotate(
            base_hitboxes,
            properties.dimensions.w,
            properties.dimensions.l,
            angle
        )
        table[angle] = rotated
        return rotated