"""
# Ontology: app.services.markets.materializer

Service for calculating dynamic crafting and construction costs.
"""
# Standard Libraries
from typing import (
    List,
    Optional
)

# Application Libraries
from app.config.settings import (
    BLUEPRINT_STRATEGIES,
    MATERIAL_PARTITIONS
)
from app.config.enums import (
    Materials,
    Chromatics,
    Orientations,
    MultiplicationStrategies
)
from app.models.config import (
    MaterialsConfiguration,
    Cost
)
from app.models.properties import Material

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Multiple
)

UNIT_FOOTPRINT = 1024.0


class Materializer:
    materials: MaterialsConfiguration

    def __init__(self, materials: MaterialsConfiguration):
        self.material = materials

    def _resolve_genus(self, material_key: str) -> Optional[str]:
        for genus, partition in MATERIAL_PARTITIONS.items():
            if material_key in partition:
                return genus
        return None

    def _material_factor(self, material_key: str, genus: Optional[str] = None) -> float:
        target_genus = genus or self._resolve_genus(material_key)
        if not target_genus:
            return 1.0
        genus_table = self.materials.genera.get(target_genus, {})
        return genus_table.get(material_key, 1.0)

    def _blueprint_factor(
        self,
        blueprint_key: Optional[str],
        schema: Optional[str]
    ) -> float:
        if not blueprint_key or not schema:
            return 1.0
        schema_table = self.materials.blueprints.get(schema, {})
        return schema_table.get(blueprint_key, 1.0)

    def _total_units(
        self,
        strategy: Optional[str],
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

        strategy = (
            BLUEPRINT_STRATEGIES.get(blueprints, MultiplicationStrategies.SIMPLE.value)
            if blueprints else MultiplicationStrategies.SIMPLE.value
        )
        total_units = self._total_units(strategy, blueprint_key, nx, ny)
        norm_area = ((dimensions.w * dimensions.l) / UNIT_FOOTPRINT) * total_units
        delta = self._blueprint_factor(blueprint_key, blueprints)

        costs: List[Cost] = []

        if materials and materials.genus == Materials.CHROMATICS.value:
            host_item = materials.host
            mu_host = self._material_factor(host_item)
            host_qty = max(1, round(norm_area * mu_host * delta))
            costs.append(Cost(item=host_item, quantity=host_qty))

            if material_key != Chromatics.NEUTRAL.value:
                mu_dye = self._material_factor(material_key, Materials.CHROMATICS.value)
                dye_qty = max(1, round(norm_area * mu_dye))
                costs.append(Cost(item=material_key, quantity=dye_qty))
            return costs

        genus = materials.genus if materials else None
        mu_mat = self._material_factor(material_key, genus)
        qty = max(1, round(norm_area * mu_mat * delta))
        costs.append(Cost(item=material_key, quantity=qty))
        return costs