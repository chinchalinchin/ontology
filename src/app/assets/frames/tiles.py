"""
# Ontology: app.assets.frames.tiles

Package for Tile Frame implementations. 

"""
# Stamdard Libraries
from typing import (
    List,
    Tuple,
    Dict
)
import logging

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    Seasons,
    Cycles,
    AnnualStages,
    PerennialStages,
    CentennialStages
)
from app.assets.base import Frame
from app.models.state import (
    AssetState,
    CalendarState
)
from app.models.properties import (
    TileProperties
)

logger = logging.getLogger(__name__)


class SeasonalFrame(Frame):
    def index(self, id: str, properties: TileProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops = {}
        for row, season in enumerate(Seasons):
            for col_cycle, cycle in enumerate(Cycles):
                for period in range(3):
                    col = col_cycle * 3 + period
                    key = settings.SEPARATOR.join([
                        id, season.value, cycle.value, str(period)
                    ])
                    crops[key] = (col * w, row * l, w, l)
        return crops

    def eras(self, id: str, calendar: CalendarState) -> List[Tuple[str, int, int]]:
        key = settings.SEPARATOR.join([
            id, 
            calendar.season, 
            calendar.cycle, 
            str(calendar.period)
        ])
        return [(key, 0, 0)]

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        # Fallback if accessed outside of macro-temporal canvas baking
        return [(
            settings.SEPARATOR.join([
                id,
                Seasons.SPRING.value,
                Cycles.ONSET.value,
                "0"
            ]),0, 0)]