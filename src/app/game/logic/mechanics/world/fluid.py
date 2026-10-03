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
    Tuple,
    List,
    TYPE_CHECKING
)

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances,
    Directions,
    Executors,
    Relations
)
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload
from app.services.generators.game.actuator import Actuator
from app.services.generators.game.cartographer import Cartographer

if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.relations.shorelines import ShorelineIndex

logger = logging.getLogger(__name__)


def _obstacle_intersects_fluid(gate: Asset, fluid: Asset) -> bool:
    """
    Evaluates whether an obstacle's AABB intersects an active fluid's compound
    hitboxes (with edge-touching tolerance) or lies within its forward emission corridor.
    """
    gx = gate.state.position.x
    gy = gate.state.position.y
    gw = gate.dimensions.w
    gl = gate.dimensions.l

    fx = fluid.state.position.x
    fy = fluid.state.position.y
    fw = fluid.properties.dimensions.w
    fl = fluid.properties.dimensions.l
    direction = fluid.state.source
    dir_val = direction.value if hasattr(direction, "value") else str(direction)

    # 1. Broad-phase edge-touching AABB check against active compound hitboxes
    for hb in fluid.hitboxes:
        hx = fx + hb.position.x
        hy = fy + hb.position.y
        hw = hb.dimensions.w
        hl = hb.dimensions.l

        # Non-strict AABB overlap (touching counts as linked)
        if (gx <= hx + hw and gx + gw >= hx and
            gy <= hy + hl and gy + gl >= hy):
            return True

    # 2. Forward emission corridor check (obstacle directly downstream of emitter)
    if dir_val == Directions.DOWN.value:
        if gx < fx + fw and gx + gw > fx and gy >= fy:
            return True
    elif dir_val == Directions.UP.value:
        if gx < fx + fw and gx + gw > fx and (gy + gl) <= fy:
            return True
    elif dir_val == Directions.RIGHT.value:
        if gy < fy + fl and gy + gl > fy and gx >= fx:
            return True
    elif dir_val == Directions.LEFT.value:
        if gy < fy + fl and gy + gl > fy and (gx + gw) <= fx:
            return True

    return False


class FluidMechanics(Mechanic):
    """
    World mechanic monitoring static gate transitions to invalidate fluid propagation
    and coordinating two-pass fluid propagation and layer shoreline generation.
    """
    _gate_states: Dict[str, bool]
    _debounce: Dict[str, int]
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
        return self.relations.get(Relations.SHORELINES.value)

    @shorelines.setter
    def shorelines(self, value: ShorelineIndex) -> None:
        self.set_relation(Relations.SHORELINES.value, value)

    def __init__(self, actuator: Optional[Actuator] = None):
        super().__init__()
        if actuator is not None:
            self.set_executor(Executors.ACTUATOR.value, actuator)
        self._gate_states = {}
        self._debounce = {}
        self._initialized = False

    @staticmethod
    def _fluid_signature(fluids: List[Asset]) -> Tuple:
        """Captures hydrological geometry state across stream lengths, pools, and branches."""
        sig = []
        for f in fluids:
            pool = f.state.pool
            pool_tuple = (pool.x, pool.y, pool.w, pool.l) if pool else None
            branches_tuple = tuple((b.position.x, b.position.y, b.length) for b in f.state.branches)
            sig.append((f.name, f.state.length, pool_tuple, branches_tuple))
        return tuple(sig)

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

        # Capture initial run state prior to mutation
        is_initial = not self._initialized
        if is_initial:
            for f in fluids:
                invalidated_layers.add(f.state.layer)

        # Gate state transitions trigger dynamic layer fluid invalidation with spatial corridor filtering
        for gate in gates:
            layer = gate.state.layer
            curr_switch = gate.state.switch
            prev_switch = self._gate_states.get(gate.name)

            if prev_switch is not None and prev_switch != curr_switch:
                self._gate_states[gate.name] = curr_switch
                self._debounce[gate.name] = settings.FLUID_INVALIDATION_DEBOUNCE_TICKS

            if gate.name in self._debounce:
                if self._debounce[gate.name] > 0:
                    self._debounce[gate.name] -= 1
                    continue
                else:
                    del self._debounce[gate.name]

                    # Spatial Bounding: Check intersection with layer fluid hitboxes or corridor
                    layer_fluids = board.instances(AssetInstances.FLUIDS.value, layer)
                    spatially_linked = any(
                        _obstacle_intersects_fluid(gate, f)
                        for f in layer_fluids
                    )

                    if spatially_linked:
                        invalidated_layers.add(layer)
                        logger.info(
                            settings.SEPARATOR.join([
                                "Telemetry:FluidMechanics",
                                "Invalidation:Gate",
                                gate.name
                            ]) + f" switch: {curr_switch}"
                        )
            else:
                self._gate_states[gate.name] = curr_switch

        for fluid in fluids:
            if fluid.state.layer in invalidated_layers:
                fluid.state.dirty = True

        dirty_fluids = [f for f in fluids if f.state.dirty]
        if not dirty_fluids and not is_initial:
            return

        dirty_layers = {f.state.layer for f in dirty_fluids}
        if is_initial:
            dirty_layers.update({f.state.layer for f in fluids})

        for layer in dirty_layers:
            layer_fluids = board.instances(AssetInstances.FLUIDS.value, layer)
            pre_sig = self._fluid_signature(layer_fluids)

            # Pass 1: Propagate fluid dynamics across all layer fluids
            for f in layer_fluids:
                logger.info(
                    f"Telemetry:FluidMechanics:PrePropagate:{f.name} "
                    f"pos=({f.state.position.x}, {f.state.position.y}) "
                    f"len={f.state.length} "
                    f"pool={f.state.pool}"
                )
                self.actuator.propagate(f, board)
            
            # Delegate layer water cache synchronization to FluidMechanics
            board.update_fluid_cache(layer)

            post_sig = self._fluid_signature(layer_fluids)
            has_shorelines = bool(board.shorelines(layer))

            # Pass 2: Synthesize layer geography if geometry shifted, during initial tick, or if missing
            if pre_sig != post_sig or is_initial or not has_shorelines:
                if self.shorelines is not None:
                    Cartographer.purge(layer, board)
                    new_shores = Cartographer.generate(layer, board, self.shorelines)
                    if new_shores:
                        board.add(new_shores)
                        logger.info(
                            f"Telemetry:FluidMechanics:GeneratedShorelines:Layer={layer} count={len(new_shores)}"
                        )
            else:
                logger.info(f"Telemetry:FluidMechanics:SkipRegeneration:Layer={layer} water geometry invariant.")

        # Finalize initialization after first full update cycle
        self._initialized = True