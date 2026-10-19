"""
# Ontology: app.services.markets.materializer

Service for calculating dynamic crafting and construction costs.
"""
from typing import List, Optional

from app.config.settings import BLUEPRINT_STRATEGIES
from app.config.enums import (
    Materials,
    Chromatics,
    MultiplicationStrategies
)
from app.models.config.markets import (
    MarketConfiguration, 
    Cost
)
from app.models.properties import Material

# Cython Libraries
from libs.core.models import Dimensions, Multiple

UNIT_FOOTPRINT = 1024.0

class Materializer:
    markets: MarketConfiguration

    def __init__(self, markets: MarketConfiguration):
        self.markets = markets

    def cost(
        self,
        dimensions: Dimensions,
        material_key: str,
        blueprint_key: str,
        materials: Optional[Material] = None,
        blueprints: Optional[str] = None,
        multiple: Optional[Multiple] = None
    ) -> List[Cost]:
        nx = multiple.nx if multiple and multiple.nx else 1
        ny = multiple.ny if multiple and multiple.ny else 1

        strategy = BLUEPRINT_STRATEGIES.get(
            blueprints,
            MultiplicationStrategies.SIMPLE.value
        )
        if strategy == MultiplicationStrategies.EXPANSION.value:
            total_units = nx * (ny + 2)
        else:
            total_units = nx * ny

        norm_area = ((dimensions.w * dimensions.l) / UNIT_FOOTPRINT) * total_units
        delta = self.markets.blueprints.get(blueprint_key, 1.0)

        costs: List[Cost] = []
        
        if materials and materials.genus == Materials.CHROMATICS.value:
            host_item = materials.host
            mu_host = self.markets.materials.get(host_item, 1.0)
            host_qty = max(1, round(norm_area * mu_host * delta))
            costs.append(Cost(item=host_item, quantity=host_qty))

            if material_key != Chromatics.NEUTRAL.value:
                mu_dye = self.markets.materials.get(material_key, 1.0)
                dye_qty = max(1, round(norm_area * mu_dye))
                costs.append(Cost(item=material_key, quantity=dye_qty))
        else:
            mu_mat = self.markets.materials.get(material_key, 1.0)
            qty = max(1, round(norm_area * mu_mat * delta))
            costs.append(Cost(item=material_key, quantity=qty))

        return costs