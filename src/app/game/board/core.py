"""
@domain.system
@app.core
@app.component

# Ontology: Source - app.game.board.core

The Board Database.
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
import app.static.settings as settings
import app.game.board.modules.predicates as predicates

from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Frequencies,
    Shortcuts
)
from app.static.loader import Loader
from app.game.board.modules.fields import MoistureField
from app.game.devices import Device
from app.game.menus.core import Menu
from app.services.generators.game.cradle import Cradle
from app.models.state.core import (
    PlotState,
    CalendarState
)
from app.models.config import ConfigurationSchema
from app.models.groups import EquipmentGroup
from app.game.board.modules.cache import Cache

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
    calendar: CalendarState
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
    _moisture_fields: Dict[str, MoistureField]

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
        self.calendar = CalendarState()
        self.menus = []
        self.overlays = []
        self.configurations = configurations
        self.equipment = equipment
        self.perimeters = {}
        self._assets = list(assets)
        self._moisture_fields: Dict[str, MoistureField] = {}
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
        instance: str = AssetInstances.ENVIRON.value
    ) -> Optional[Asset]:
        return self._cache.get_tile(layer, position, instance)


    def character(self, name: str) -> Any:
        return self._cache.get_character(name)


    def characters(self) -> Dict[str, Any]:
        return self._cache.get_characters()


    def asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
        search_list = self.renderables(layer) if layer else self._assets
        return next((a for a in search_list if a.name == name), None)


    def assets(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        if layer is not None:
            target_assets = self._cache.get_layer_assets(layer)
        else:
            target_assets = self._assets

        if elevation is not None:
            return [a for a in target_assets if a.elevation == elevation]
        return target_assets


    def weights(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        weights = self._cache.get_weights(layer) if layer is not None else [
            a for a in self._assets if predicates.is_weight(a)
        ]
        if elevation is not None:
            target_e = max(0, elevation)
            return [w for w in weights if target_e in w.hitbox.elevations(w.properties, w.state)]
        return weights
    

    def obstacles(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        obstacles = self._cache.get_obstacles(layer) if layer is not None else []
        if elevation is not None:
            target_e = max(0, elevation)
            return [o for o in obstacles if target_e in o.hitbox.elevations(o.properties, o.state)]
        return obstacles
    

    def bridges(self, layer: Optional[str] = None) -> List[Asset]:
        """Retrieves static sensor bridge assets for a specific layer or across all layers."""
        return self.instances(AssetInstances.BRIDGES.value, layer)


    def layers(self) -> List[str]:
        return self._cache.get_layers()


    def categories(self, category: str, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        cat_assets = self._cache.get_categories(category, layer)
        if elevation is not None:
            return [a for a in cat_assets if a.elevation == elevation]
        return cat_assets

    
    def instances(self, instance: str, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        inst_assets = self._cache.get_instances(instance, layer)
        if elevation is not None:
            return [a for a in inst_assets if a.elevation == elevation]
        return inst_assets


    def renderables(self, layer: Optional[str] = None) -> List[Asset]:
        if layer is None:
            return [asset for asset in self._assets if asset.category != AssetCategories.TILES.value]
        return self._cache.get_renderables(layer)


    def shorelines(self, layer: Optional[str] = None) -> List[Asset]:
        """
        Retrieves active procedural shoreline assets for a specific layer or across all layers.
        """
        if layer is not None:
            return self._cache.get_shorelines(layer)
        return self.instances(AssetInstances.SHORELINES.value)

    
    def moisture(self, layer: str, x: int, y: int) -> float:
        """
        Queries scalar moisture potential at coordinates (x, y) on the specified layer.
        """
        field = self._moisture_fields.get(layer)
        if not field:
            return 0.0
        return field.evaluate(x, y)


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

    def set_moisture_field(self, layer: str, field: MoistureField) -> None:
        """
        Stores the compiled MoistureField for the layer and precomputes
        moisture_flux directly on all static ResourceState instances.
        """
        self._moisture_fields[layer] = field
        resources = self.categories(AssetCategories.RESOURCES.value, layer)
        for resource in resources:
            if resource.state.position:
                flux = field.evaluate(
                    resource.state.position.x,
                    resource.state.position.y
                )
                resource.state.moisture_flux = flux
                logger.debug(
                    f"Board: Layer={layer} resource='{resource.name}' at "
                    f"({resource.state.position.x}, {resource.state.position.y}) "
                    f"moisture_flux={flux:.4f}"
                )
        logger.info(
            f"Board: Layer={layer} MoistureField cached across {len(resources)} resources."
        )


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
            self._cache.rebuild_fluid(layer)


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
        self._moisture_fields.clear()

    # ------------------------------------------------ EXPORTERS

    def serialize(self, slot: str) -> None:
        dump: Dict[str, Any] = {}

        for asset in self._assets:
            if asset.category == AssetCategories.WIDGETS.value:
                continue

            if asset.category == AssetCategories.EFFECTS.value:
                frequency = getattr(asset.properties, "frequency", None)
                if asset.properties.frequency and \
                    asset.properties.frequency.type == Frequencies.TEMPORARY.value and \
                    not asset.properties.frequency.persist:
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

        # Serialize abstract world metadata (resolving Bug B015)
        if self.calendar:
            dump[Shortcuts.CALENDAR.value] = asdict(self.calendar)
        if self.plot:
            dump[Shortcuts.PLOTS.value] = asdict(self.plot) if hasattr(self.plot, "__dataclass_fields__") else self.plot

        Loader.save_state(slot, dump)