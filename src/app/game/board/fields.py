"""
# Ontology: app.game.board.fields

Continuous environmental potential field models obeying linear superposition.
"""
# Standard Libraries
import math
from typing import (
    List,
    Tuple
)
from dataclasses import dataclass, field

# Application Libraries
import app.config.settings as settings


@dataclass(slots=True)
class StreamSegment:
    x1: float
    y1: float
    x2: float
    y2: float
    flow: int


@dataclass(slots=True)
class PoolSource:
    cx: float
    cy: float
    radius: float
    flow: int


class MoistureField:
    """
    Continuous 2D hydrological potential field obeying linear superposition.
    Evaluates moisture concentration from linear stream corridors and annular pools
    using screened exponential distance attenuation.
    """
    _streams: List[StreamSegment]
    _pools: List[PoolSource]
    sigma: float
    phi_0: float

    def __init__(
        self,
        sigma: float = getattr(settings, "MOISTURE_DECAY_SIGMA", 64.0),
        phi_0: float = getattr(settings, "BASE_MOISTURE_POTENTIAL", 1.0)
    ):
        self._streams = []
        self._pools = []
        self.sigma = sigma
        self.phi_0 = phi_0

    def add_stream(self, x1: float, y1: float, x2: float, y2: float, flow: int) -> None:
        """
        Registers a directional fluid stream corridor or branch line segment.
        """
        if flow > 0:
            self._streams.append(StreamSegment(x1, y1, x2, y2, flow))

    def add_pool(self, cx: float, cy: float, radius: float, flow: int) -> None:
        """
        Registers an isotropic annular pool disk source.
        """
        if flow > 0:
            self._pools.append(PoolSource(cx, cy, radius, flow))

    def evaluate(self, x: float, y: float) -> float:
        """
        Evaluates cumulative moisture potential at target coordinate (x, y)
        via superposition across all registered linear and disk sources.
        """
        total_flux = 0.0

        # 1. Superposition of linear stream corridors
        for stream in self._streams:
            dx = stream.x2 - stream.x1
            dy = stream.y2 - stream.y1
            len_sq = dx * dx + dy * dy

            if len_sq == 0.0:
                dist = math.hypot(x - stream.x1, y - stream.y1)
            else:
                t = max(0.0, min(1.0, ((x - stream.x1) * dx + (y - stream.y1) * dy) / len_sq))
                proj_x = stream.x1 + t * dx
                proj_y = stream.y1 + t * dy
                dist = math.hypot(x - proj_x, y - proj_y)

            cutoff = self.sigma * stream.flow
            if dist <= cutoff:
                total_flux += self.phi_0 * stream.flow * math.exp(-dist / self.sigma)

        # 2. Superposition of annular pool disks
        for pool in self._pools:
            dist_to_center = math.hypot(x - pool.cx, y - pool.cy)
            dist = max(0.0, dist_to_center - pool.radius)
            cutoff = self.sigma * pool.flow
            if dist <= cutoff:
                total_flux += self.phi_0 * pool.flow * math.exp(-dist / self.sigma)

        return total_flux

    def clear(self) -> None:
        """
        Clears all registered stream and pool sources.
        """
        self._streams.clear()
        self._pools.clear()