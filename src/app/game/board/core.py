"""
# Ontology: app.game.board.core

Module for the game database class, Board.
"""
# Standard Libraries
import logging
from typing import (
    List,
    Dict,
    Tuple,
    Any,
    Optional
)
from dataclasses import asdict

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories,
    AssetInstances,
    Lifecycles
)
from app.config.loader import Loader
from app.game.devices import Device
from app.game.menus.core import Menu
from app.services.generators.game.cradle import Cradle
from app.models.state.core import PlotState
from app.models.config import ConfigurationSchema
from app.models.groups import EquipmentGroup
from app.game.board.cache import Cache
import app.game.board.predicates as predicates

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Boundary
)

logger = logging.getLogger(__name__)


class Board:
    """
    ## Board

    Central database for the game Engine. Holds all Asset state and configuration,
    and provides queryable interfaces for Mechanics to retrieve pertinent game data.
    """
    # ------- Public Fields
    # Flags
    loaded: bool
    paused: bool
    # Game Data
    plot: PlotState
    perimeters: Dict[str, List[Boundary]]
    # Configurations
    configurations: ConfigurationSchema
    equipment: EquipmentGroup
    # Game Components
    device: Device
    cradle: Cradle
    menus: List[Menu]
    overlays: List[Menu]
    # ------- Private Fields
    _assets: List[Asset]
    _cache: Cache

    def __init__(
        self,
        assets: List[Asset],
        configurations: ConfigurationSchema,
        equipment: EquipmentGroup
    ):
        logger.info(f"Initializing Board with {len(assets)} incoming assets.")
        self.loaded = False
        self.paused = False
        self.plot = None
        self.device = None
        self.cradle = None
        self.menus = []
        self.overlays = []
        self.configurations = configurations
        self.equipment = equipment
        self.perimeters = {}
        self._assets = list(assets)
        self._cache = Cache()
        self._cache.index_batch(self._assets)
        logger.info("Board completely hydrated and initialized.")

    # ---------------------------------------------------------
    # ------------------------------------ BACKWARD COMPATIBILITY
    # Properties for internal components/tests inspecting cache internals directly

    @property
    def _cached_categories(self) -> Dict[str, Dict[str, List[Asset]]]:
        return self._cache.cached_categories

    @property
    def _cached_instances(self) -> Dict[str, Dict[str, List[Asset]]]:
        return self._cache.cached_instances

    @property
    def _cached_layers(self) -> Dict[str, List[Asset]]:
        return self._cache.cached_layers

    @property
    def _cached_renderables(self) -> Dict[str, List[Asset]]:
        return self._cache.cached_renderables

    @property
    def _cached_weights(self) -> Dict[str, List[Asset]]:
        return self._cache.cached_weights

    @property
    def _cached_tilemap(self) -> Dict[str, Dict[str, Dict[Tuple[int, int], Asset]]]:
        return self._cache.cached_tilemap

    @property
    def _cached_fluidmap(self) -> Dict[str, Dict[Tuple[int, int], List[Asset]]]:
        return self._cache.cached_fluidmap

    @property
    def _cached_characters(self) -> Dict[str, Any]:
        return self._cache.cached_characters

    @property
    def _all_categories(self) -> Dict[str, List[Asset]]:
        return self._cache.all_categories

    @property
    def _all_instances(self) -> Dict[str, List[Asset]]:
        return self._cache.all_instances

    @property
    def _shorelines(self) -> Dict[str, List[Asset]]:
        return self._cache.shorelines

    # ---------------------------------------------------------
    # ---------------------------------------------- PREDICATES

    def fluid(
        self,
        layer: str,
        position: Position,
        exclude: Optional[str] = None
    ) -> bool:
        """
        Evaluates whether Cartesian coordinate (pos.x, pos.y) intersects an active
        fluid stream corridor or annular pool on the layer.
        Uses O(1) broad-phase spatial hash lookup followed by narrow-phase AABB validation.
        """
        cx = int(position.x) // settings.TILE_HASH_SIZE
        cy = int(position.y) // settings.TILE_HASH_SIZE
        bucket = self._cache.get_fluid_bucket(layer, cx, cy)
        if not bucket:
            return False

        for fluid in bucket:
            if exclude and fluid.name == exclude:
                continue

            if predicates.in_fluid(position, fluid):
                return True

        return False

    # ------------------------------------------------ SETTERS

    def set_device(self, device: Device) -> None:
        self.device = device

    def set_cradle(self, cradle: Cradle) -> None:
        self.cradle = cradle

    def set_overlays(self, overlays: List[Menu]) -> None:
        self.overlays = overlays

    def set_plot(self, plot: str) -> None:
        self.plot = plot

    # ------------------------------------------------ GETTERS

    def player(self, slot: int = 0) -> Optional[Asset]:
        players = self._cache.get_instances(AssetInstances.PLAYERS.value)
        if not players:
            return None
        if slot < len(players):
            return players[slot]
        return players[0]

    def tile(
        self,
        layer: str,
        position: Position,
        instance: str = AssetInstances.BACK.value
    ) -> Optional[Asset]:
        return self._cache.get_tile(layer, position, instance)

    def character(self, name: str) -> Any:
        return self._cache.get_character(name)

    def characters(self) -> Dict[str, Any]:
        return self._cache.get_characters()

    def asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
        search_list = self.renderables(layer) if layer else self._assets
        return next((a for a in search_list if a.name == name), None)

    def assets(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is None:
            return self._assets
        return self._cache.get_layer_assets(layer)

    def weights(self, layer: Optional[str] = None) -> List[Asset]:
        """Returns physical weight assets (m >= 0) on the layer."""
        if layer is None:
            return [asset for asset in self._assets if predicates.is_weight(asset)]
        return self._cache.get_weights(layer)

    def obstacles(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is None:
            return []
        return self._cache.get_obstacles(layer)

    def bridges(self, layer: Optional[str] = None) -> List[Asset]:
        """Retrieves static sensor bridge assets for a specific layer or across all layers."""
        return self.instances(AssetInstances.BRIDGES.value, layer)

    def layers(self) -> List[str]:
        return self._cache.get_layers()

    def categories(self, category: str, layer: Optional[str] = None) -> List[Asset]:
        return self._cache.get_categories(category, layer)

    def instances(self, instance: str, layer: Optional[str] = None) -> List[Asset]:
        return self._cache.get_instances(instance, layer)

    def renderables(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is None:
            return [asset for asset in self._assets if asset.category != AssetCategories.TILES.value]
        return self._cache.get_renderables(layer)

    def shorelines(self, layer: Optional[str] = None) -> List[Asset]:
        """
        Retrieves active procedural shoreline assets for a specific layer or across all layers.
        """
        return self._cache.get_shorelines(layer)

    def size(self, layer: Optional[str] = None) -> List[Dimensions]:
        layers = [layer] if layer is not None else self.layers()
        layer_sizes = []

        for l in layers:
            layer_assets = self.assets(l)
            max_w = 0
            max_l = 0

            for asset in layer_assets:
                if asset.category == AssetCategories.TILES.value:
                    ext_w = int(asset.state.position.x) + (asset.state.multiple.nx * asset.properties.dimensions.w)
                    ext_l = int(asset.state.position.y) + (asset.state.multiple.ny * asset.properties.dimensions.l)
                elif asset.dimensions:
                    ext_w = int(asset.state.position.x) + asset.dimensions.w
                    ext_l = int(asset.state.position.y) + asset.dimensions.l
                else:
                    continue

                if ext_w > max_w:
                    max_w = ext_w
                if ext_l > max_l:
                    max_l = ext_l

            layer_sizes.append(Dimensions(w=max_w, l=max_l))

        return layer_sizes

    # ------------------------------------------------ MUTATORS

    def update_fluid_cache(self, layer: str) -> None:
        """
        Rebuilds the O(1) spatial fluid grid cache for the specified layer.
        """
        self._cache.rebuild_fluid(layer)

    def cache_fluid(self, fluid: Asset) -> None:
        """
        Updates the spatial self._cache grid cache for the specified fluid's layer.
        """
        layer = fluid.state.layer
        if layer:
            self._cache.rebuild_self._cache(layer)

    def relayer(self, asset: Asset, new_layer: str) -> None:
        self._cache.relayer(asset, new_layer)

    def add(self, additions: List[Asset]) -> None:
        for asset in additions:
            self._assets.append(asset)
            logger.info(
                f"Appending Asset(id={asset.id}, "
                f"name={asset.name}, "
                f"category={asset.category}, "
                f"instance={asset.instance})"
            )
        self._cache.index_batch(additions)

    def remove(self, removals: List[Asset]) -> None:
        """
        Performs bulk entity de-registration.
        """
        if not removals:
            return

        removal_set = set(removals)
        self._assets = [a for a in self._assets if a not in removal_set]
        self._cache.evict_batch(removals)

    def clear(self) -> None:
        self._assets.clear()
        self._cache.clear()
        self.menus.clear()
        self.overlays.clear()
        self.perimeters.clear()

    # ------------------------------------------------ EXPORTERS

    def serialize(self, slot: str) -> None:
        dump: dict[str, dict[str, list[dict[str, Any]]]] = {}

        for asset in self._assets:
            if asset.category == AssetCategories.WIDGETS.value:
                continue

            if asset.category == AssetCategories.EFFECTS.value:
                lifecycle = getattr(asset.properties, "lifecycle", None)
                if lifecycle and lifecycle.type == Lifecycles.TEMPORARY.value and not lifecycle.persist:
                    continue

            if asset.category == AssetCategories.SHEETS.value and asset.instance not in (
                AssetInstances.SPRITES.value,
                AssetInstances.PLAYERS.value,
                AssetInstances.PIXIES.value
            ):
                continue

            cat = str(asset.category)
            inst = str(asset.instance)

            if cat not in dump:
                dump[cat] = {}
            if inst not in dump[cat]:
                dump[cat][inst] = []

            dump[cat][inst].append(asdict(asset.state))

        Loader.save_state(slot, dump)