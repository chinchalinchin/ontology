"""
# Ontology: app.game.logic.mechanics.world.fluid
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import Dict, Set, Tuple, TYPE_CHECKING

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    AssetInstances,
    MechanicExecutors
)
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload
from app.services.generators.game.actuator import Actuator

if TYPE_CHECKING:
    from app.game.board import Board

logger = logging.getLogger(__name__)


class FluidMechanics(Mechanic):
    """
    World mechanic monitoring dynamic obstacle velocities and gate switch
    transitions to invalidate and recalculate fluid propagation.
    """
    _crate_positions: Dict[str, Tuple[int, int]]
    _gate_states: Dict[str, bool]

    @property
    def actuator(self) -> Actuator:
        return self.executors[MechanicExecutors.ACTUATOR.value]
    
    def __init__(self):
        super().__init__()
        self._crate_positions = {}
        self._gate_states = {}

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        fluids = board.instances(AssetInstances.FLUIDS.value)
        if not fluids:
            return

        crates = board.instances(AssetInstances.CRATES.value)
        gates = board.instances(AssetInstances.GATES.value)
        invalidated_layers: Set[str] = set()

        for crate in crates:
            layer = crate.state.layer
            vx = crate.state.velocity.vx
            vy = crate.state.velocity.vy
            curr_pos = (crate.state.position.x, crate.state.position.y)
            prev_pos = self._crate_positions.get(crate.name)

            if abs(vx) > 0 or abs(vy) > 0 or (prev_pos is not None and prev_pos != curr_pos):
                invalidated_layers.add(layer)
                logger.info(
                    settings.SEPARATOR.join([
                        "Telemetry:FluidMechanics",
                        "Invalidation:Crate",
                        crate.name
                    ]) + f" at {curr_pos}"
                )

            self._crate_positions[crate.name] = curr_pos

        for gate in gates:
            layer = gate.state.layer
            curr_switch = gate.state.switch
            prev_switch = self._gate_states.get(gate.name)

            if prev_switch is not None and prev_switch != curr_switch:
                invalidated_layers.add(layer)
                logger.info(
                    settings.SEPARATOR.join([
                        "Telemetry:FluidMechanics",
                        "Invalidation:Gate",
                        gate.name
                    ]) + f" switch: {curr_switch}"
                )

            self._gate_states[gate.name] = curr_switch

        for fluid in fluids:
            if fluid.state.layer in invalidated_layers:
                fluid.state.dirty = True

            if fluid.state.dirty:
                self.actuator.pump(fluid, board)