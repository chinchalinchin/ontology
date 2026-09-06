"""
# Ontology: app.game.logic.mechanics.world.plot
"""
import collections
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.game.board import Board
    
from app.game.logic.mechanics.core import Mechanic
from app.models.state import DevicePayload
from app.services.translators.base import Executor

logger = logging.getLogger(__name__)

class PlotMechanics(Mechanic):
    """
    Evaluates global Plot transitions via the ISL executor against game world state.
    """
    executor: Executor = None
    
    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        if not self.executor or not board.plot.current:
            return
            
        current_plot = board.plot.current
        sprites_dict = board.characters()
        
        # Evaluate Plot ISL Conditions
        next_plot_str = self.executor.evaluate(
            current_state=current_plot,
            locals={'sprites': sprites_dict, 'board': board}
        )
        
        if next_plot_str and next_plot_str != current_plot:
            logger.info(f"Plot advancing from '{current_plot}' to '{next_plot_str}'")
            if board.plot.previous:
                board.plot.previous.append(current_plot)
            board.plot.current = next_plot_str