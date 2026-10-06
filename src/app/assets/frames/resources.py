"""
# Ontology: app.assets.frames.resources

Package for Resource Frame implementations. 

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
    Lifespans,
    AnnualStages,
    PerennialStages,
    CentennialStages
)
from app.assets.base import Frame
from app.models.state import (
    AssetState
)
from app.models.properties import (
    ResourceProperties
)

logger = logging.getLogger(__name__)


class StageFrame(Frame):
    """
    Indexes horizontal sprite strips based on the stage space 
    encoded by the asset's lifespan property.
    """

    @staticmethod
    def _stages(lifespan: str):
        if lifespan == Lifespans.ANNUAL.value:
            return AnnualStages
        if lifespan == Lifespans.PERENNIAL.value:
            return PerennialStages
        if lifespan == Lifespans.CENTENNIAL.value:
            return CentennialStages

    def index(self, id: str, properties: ResourceProperties) -> Dict[str, Tuple[int, int, int, int]]:
        w = properties.dimensions.w
        l = properties.dimensions.l
        stages = StageFrame._stages(properties.lifespan)
        
        return {
            settings.SEPARATOR.join([id, stage.value]): (i * w, 0, w, l)
            for i, stage in enumerate(stages)
        }

    def keys(self, id: str, state: AssetState) -> List[Tuple[str, int, int]]:
        return [(settings.SEPARATOR.join([id, state.stage]), 0, 0)]