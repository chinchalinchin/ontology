"""
@workflow.compositions

# Ontology: Source - app.game.logic.relations.materials

Relational index compiling Material genera, Blueprint schemas, multiplication
strategies, obstacle predicates, and intra-tier Substrates.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Tuple,
    Optional,
    FrozenSet,
    Set,
    TYPE_CHECKING
)
import logging

# Application Libraries
from app.assets.base import Singleton
from app.static.semantics import (
    AssetInstances,
    LayerProjections,
    MultiplicationStrategies,
    Substrates
)

if TYPE_CHECKING:
    from app.models.config.materials import MaterialsConfiguration

logger = logging.getLogger(__name__)


class MaterialIndex(Singleton):
    """
    Compiled relational index for Material and Blueprint spaces.
    """
    _material_partitions: Dict[str, Tuple[str, ...]]
    _material_weights: Dict[str, Dict[str, float]]
    _material_to_genus: Dict[str, str]
    _genus_host: Dict[str, Optional[str]]
    _blueprint_partitions: Dict[str, Tuple[str, ...]]
    _blueprint_strategies: Dict[str, Optional[str]]
    _blueprint_deltas: Dict[str, Dict[str, float]]
    _obstacle_blueprints: FrozenSet[str]
    _instance_substrates: Dict[str, int]
    _blueprint_substrates: Dict[str, int]

    def __init__(self):
        if not hasattr(self, "_material_partitions"):
            self._material_partitions = {}
            self._material_weights = {}
            self._material_to_genus = {}
            self._genus_host = {}
            self._blueprint_partitions = {}
            self._blueprint_strategies = {}
            self._blueprint_deltas = {}
            self._obstacle_blueprints = frozenset()
            self._instance_substrates = {}
            self._blueprint_substrates = {}

    @classmethod
    def from_configuration(cls, config: MaterialsConfiguration) -> MaterialIndex:
        """
        Compiles relational lookup tables from MaterialConfiguration.
        """
        index = cls()
        index._material_partitions = {}
        index._material_weights = {}
        index._material_to_genus = {}
        index._genus_host = {}
        index._blueprint_partitions = {}
        index._blueprint_strategies = {}
        index._blueprint_deltas = {}
        index._instance_substrates = dict(config.substrates)
        index._blueprint_substrates = {}

        obstacles: Set[str] = set()

        # 1. Compile Material Genera, Host Genus & Partitions in a single pass
        for genus, mat_part in config.genera.items():
            ordered_keys = tuple(mat_part.partitions.keys())
            index._material_partitions[genus] = ordered_keys
            index._material_weights[genus] = dict(mat_part.partitions)
            index._genus_host[genus] = mat_part.host
            for mat_key in ordered_keys:
                index._material_to_genus[mat_key] = genus

        # 2. Compile Blueprint Schemas, Strategies, Obstacles & Substrates
        for schema, bp_part in config.blueprints.items():
            ordered_bps = tuple(bp_part.partitions.keys())
            index._blueprint_partitions[schema] = ordered_bps
            index._blueprint_strategies[schema] = bp_part.strategy
            index._blueprint_deltas[schema] = {}

            for bp_key, spec in bp_part.partitions.items():
                index._blueprint_deltas[schema][bp_key] = spec.delta
                index._blueprint_substrates[bp_key] = spec.substrate
                if spec.obstacle:
                    obstacles.add(bp_key)

        index._obstacle_blueprints = frozenset(obstacles)
        return index

    def materials(self, genus: str) -> Tuple[str, ...]:
        return self._material_partitions.get(genus, ())

    def host(self, genus: str) -> Optional[str]:
        """Returns the single host genus key for a material genus, or None."""
        return self._genus_host.get(genus)

    def hosts(self, genus: str) -> Tuple[str, ...]:
        """Returns the partition tuple of valid host materials for a genus."""
        host_genus = self._genus_host.get(genus)
        if not host_genus:
            return ()
        return self._material_partitions.get(host_genus, ())

    def blueprints(self, schema: str) -> Tuple[str, ...]:
        return self._blueprint_partitions.get(schema, ())

    def strategy(self, schema: Optional[str]) -> str:
        if not schema:
            return MultiplicationStrategies.SIMPLE.value
        return (
            self._blueprint_strategies.get(schema)
            or MultiplicationStrategies.SIMPLE.value
        )

    def is_obstacle(self, blueprint: Optional[str]) -> bool:
        if not blueprint:
            return False
        return blueprint in self._obstacle_blueprints

    def substrate(
        self,
        instance: str,
        blueprint: Optional[str] = None,
        projection: Optional[str] = None
    ) -> int:
        if (
            instance == AssetInstances.DOORS.value
            and projection == LayerProjections.OUT.value
        ):
            return Substrates.OVERLAYS.value
        if instance == AssetInstances.STRUTS.value and blueprint:
            return self._blueprint_substrates.get(blueprint, Substrates.STANDARD.value)
        return self._instance_substrates.get(instance, Substrates.STANDARD.value)

    def material_weight(
        self,
        material_key: str,
        genus: Optional[str] = None
    ) -> float:
        target_genus = genus or self._material_to_genus.get(material_key)
        if not target_genus:
            return 1.0
        return self._material_weights.get(target_genus, {}).get(material_key, 1.0)

    def blueprint_delta(
        self,
        schema: Optional[str],
        blueprint_key: Optional[str]
    ) -> float:
        if not schema or not blueprint_key:
            return 1.0
        return self._blueprint_deltas.get(schema, {}).get(blueprint_key, 1.0)