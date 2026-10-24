"""
# Ontology: Source - app.game.logic.mechanics.core.telemetry
"""
from __future__ import annotations

# Standard Libraries
import re
from typing import (
    Dict, 
    Any, 
    List,
    TYPE_CHECKING
)

# Application Libraries
from app.assets.base import Asset
from app.game.logic.mechanics.base import Mechanic

if TYPE_CHECKING:
    from app.game.board import Board

class TelemetryMechanics(Mechanic):
    def __init__(self, inbound_queue):
        self.inbound_queue = inbound_queue

    def update(self, board: Board, delta: float, bus=None, payload=None) -> None:
        # Non-blocking resolution of pending requests on tick boundary
        while not self.inbound_queue.empty():
            try:
                request = self.inbound_queue.get_nowait()
            except Exception:
                break

            query = request.query
            if query == "assets":
                request.response = {"assets": self._query_assets(board, request.params)}
            elif query == "metrics":
                request.response = {
                    "loaded": board.loaded,
                    "paused": board.paused,
                    "calendar": {
                        "season": board.calendar.season,
                        "cycle": board.calendar.cycle,
                        "period": board.calendar.period,
                    },
                    "asset_count": len(board.assets()),
                }
            elif query == "hydrology":
                layer = request.params.get("layer", "0")
                x = int(request.params.get("x", 0))
                y = int(request.params.get("y", 0))
                request.response = {
                    "moisture": board.moisture(layer, x, y),
                }
            else:
                request.response = {"error": f"unknown_query: {query}"}

            request.done.set()

    def _query_assets(self, board: Board, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        assets = board.assets()
        for key in ("category", "instance", "id", "name"):
            pattern = params.get(key)
            if pattern:
                regex = re.compile(pattern)
                assets = [a for a in assets if regex.search(getattr(a, key, "") or "")]

        # Return minimal primitive representations without deep object traversal
        return [
            {
                "id": a.id,
                "name": a.name,
                "category": a.category,
                "instance": a.instance,
                "x": a.state.position.x if a.state and a.state.position else None,
                "y": a.state.position.y if a.state and a.state.position else None,
            }
            for a in assets
            if a.category != "widgets"
        ]