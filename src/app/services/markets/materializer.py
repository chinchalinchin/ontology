"""
@app.service
@modality.material
@workflow.compositions

# Ontology: Source - app.services.markets.materializer

Service for calculating dynamic crafting and construction costs via MaterialIndex.
"""
# Standard Libraries
from typing import (
    List,
    Optional
)

# Application Libraries
from app.static.semantics import (
    Materials,
    Chromatics,
    Orientations,
    MultiplicationStrategies
)
from app.game.logic.relations.materials import MaterialIndex
from app.models.config.materials import Cost
from app.models.properties import Material

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Multiple
)

UNIT_FOOTPRINT = 1024.0


class Materializer:
    materials: MaterialIndex

    def __init__(self, materials: MaterialIndex):
        self.materials = materials

    def _total_units(
        self,
        strategy: str,
        blueprint_key: Optional[str],
        nx: int,
        ny: int
    ) -> int:
        if strategy == MultiplicationStrategies.EXPANSION.value:
            return nx * (ny + 2)
        if strategy == MultiplicationStrategies.PERIMETER.value:
            return 2 * (nx + ny + 2)
        if strategy == MultiplicationStrategies.ORIENTED.value:
            return nx if blueprint_key == Orientations.HORIZONTAL.value else ny
        return nx * ny

    def cost(
        self,
        dimensions: Dimensions,
        material_key: str,
        blueprint_key: Optional[str] = None,
        materials: Optional[Material] = None,
        blueprints: Optional[str] = None,
        multiple: Optional[Multiple] = None
    ) -> List[Cost]:
        nx = multiple.nx if multiple and multiple.nx else 1
        ny = multiple.ny if multiple and multiple.ny else 1

        strategy = self.materials.strategy(blueprints)
        total_units = self._total_units(strategy, blueprint_key, nx, ny)
        norm_area = ((dimensions.w * dimensions.l) / UNIT_FOOTPRINT) * total_units
        delta = self.materials.blueprint_delta(blueprints, blueprint_key)

        costs: List[Cost] = []

        if materials and materials.genus == Materials.CHROMATICS.value:
            host_item = materials.host
            mu_host = self.materials.material_weight(host_item)
            host_qty = max(1, round(norm_area * mu_host * delta))
            costs.append(Cost(item=host_item, quantity=host_qty))

            if material_key != Chromatics.NEUTRAL.value:
                mu_dye = self.materials.material_weight(
                    material_key,
                    Materials.CHROMATICS.value
                )
                dye_qty = max(1, round(norm_area * mu_dye))
                costs.append(Cost(item=material_key, quantity=dye_qty))
            return costs

        genus = materials.genus if materials else None
        mu_mat = self.materials.material_weight(material_key, genus)
        qty = max(1, round(norm_area * mu_mat * delta))
        costs.append(Cost(item=material_key, quantity=qty))
        return costs