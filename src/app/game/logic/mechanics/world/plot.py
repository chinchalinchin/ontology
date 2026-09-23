"""
# Ontology: app.game.logic.mechanics.world.plot
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import TYPE_CHECKING, Optional

# Application Libraries
from app.config.enums import MechanicExecutors
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload
from app.services.translators.base import Executor

if TYPE_CHECKING:
    from app.game.board import Board
    
logger = logging.getLogger(__name__)


class PlotMechanics(Mechanic):
    """
    Evaluates global Plot transitions via the ISL executor against game world state.
    """
    @property
    def executor(self) -> Optional[Executor]:
        return self.executors.get(MechanicExecutors.PLOT.value)

    @executor.setter
    def executor(self, executor: Optional[Executor]) -> None:
        if executor is None:
            self.executors.pop(MechanicExecutors.PLOT.value, None)
        else:
            self.executors[MechanicExecutors.PLOT.value] = executor

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        if not self.executor or not board.plot or not board.plot.current:
            return
            
        current_plot = board.plot.current
        sprites_dict = board.characters()
        
        # Evaluate Plot ISL Conditions
        next_plot_str = self.executor.evaluate(
            current_state=current_plot,
            locals={'sprites': sprites_dict, 'board': board}
        )
        
        if next_plot_str and next_plot_str != current_plot:
            logger.info(f"Transition(plot): {current_plot} -> {next_plot_str}")
            if board.plot.previous:
                board.plot.previous.append(current_plot)
            board.plot.current = next_plot_str