"""
# Ontology: app.game.logic.mechanics.world.fluid
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import (
    Dict, 
    Set, 
    Optional,
    TYPE_CHECKING
)

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    AssetInstances,
    Executors
)
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload
from app.services.generators.game.actuator import Actuator
from app.services.generators.game.cartographer import Cartographer

if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.relations.shorelines import ShorelineIndex

logger = logging.getLogger(__name__)


class FluidMechanics(Mechanic):
    """
    World mechanic monitoring static gate transitions to invalidate fluid propagation
    and coordinating two-pass fluid propagation and layer shoreline generation.
    """
    _gate_states: Dict[str, bool]
    _initialized: bool


    @property
    def actuator(self) -> Actuator:
        if Executors.ACTUATOR.value not in self.executors:
            self.executors[Executors.ACTUATOR.value] = Actuator()
        return self.executors[Executors.ACTUATOR.value]


    @actuator.setter
    def actuator(self, value: Actuator) -> None:
        self.executors[Executors.ACTUATOR.value] = value


    @property
    def shorelines(self) -> Optional[ShorelineIndex]:
        from app.config.enums import Relations
        return self.relations.get(Relations.SHORELINES.value)


    @shorelines.setter
    def shorelines(self, value: ShorelineIndex) -> None:
        from app.config.enums import Relations
        self.set_relation(Relations.SHORELINES.value, value)


    def __init__(self, actuator: Optional[Actuator] = None):
        super().__init__()
        if actuator is not None:
            self.set_executor(Executors.ACTUATOR.value, actuator)
        self._gate_states = {}
        self._initialized = False


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

        gates = board.instances(AssetInstances.GATES.value)
        invalidated_layers: Set[str] = set()

        # Enforce two-pass synchronization on initial engine update
        if not self._initialized:
            for f in fluids:
                invalidated_layers.add(f.state.layer)
            self._initialized = True

        # Gate state transitions trigger dynamic layer fluid invalidation (Fix B011)
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

        dirty_fluids = [f for f in fluids if f.state.dirty]
        if not dirty_fluids:
            return

        dirty_layers = {f.state.layer for f in dirty_fluids}
        for layer in dirty_layers:
            layer_fluids = board.instances(AssetInstances.FLUIDS.value, layer)
            # Pass 1: Propagate fluid dynamics across all layer fluids
            for f in layer_fluids:
                logger.info(
                    f"Telemetry:FluidMechanics:PrePropagate:{f.name} pos=({f.state.position.x}, {f.state.position.y}) "
                    f"len={f.state.length} pool={f.state.pool}"
                )
                self.actuator.propagate(f, board)
            
            # Delegate layer water cache synchronization to FluidMechanics
            board.update_fluid_cache(layer)

            # Pass 2: Synthesize layer geography across settled water boundaries
            if self.shorelines is not None:
                Cartographer.purge(layer, board)
                new_shores = Cartographer.generate(layer, board, self.shorelines)
                if new_shores:
                    board.add(new_shores)