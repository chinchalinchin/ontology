"""
@domain.system
@app.board
@app.core
@app.component

# Ontology: Source - app.game.board.core

The Board Database.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    List,
    Dict,
    Any,
    Optional,
    TYPE_CHECKING
)

# Application Libraries
import app.static.settings as settings
import app.game.logic.predicates as predicates

from app.assets.base import Asset
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Frequencies,
    LayerProjections,
    Shortcuts
)
from app.static.loader import Loader
from app.game.logic.modules.fields import MoistureField
from app.game.devices import Device
from app.game.menus.core import Menu
from app.models.adapters import serialize
from app.models.state.core import (
    AssetState,
    PlotState,
    CalendarState
)
from app.models.configurations import ConfigurationSchema
from app.models.groups import EquipmentGroup
from app.game.board.modules.cache import Cache

if TYPE_CHECKING:
    from app.services.generators.game import Cradle
    from app.services.orchestration.migrator import Migrator

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
    plot: Optional[PlotState]
    calendar: CalendarState
    perimeters: Dict[str, Dict[int, List[Boundary]]]
    # Configurations
    configurations: ConfigurationSchema
    equipment: EquipmentGroup
    # Game Components
    device: Optional[Device]
    cradle: Optional[Cradle]
    materializer: Optional[Any]
    migrator: Optional[Migrator]
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
        self.materializer = None
        self.migrator = None
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


    def set_plot(self, plot: PlotState) -> None:
        self.plot = plot


    def set_migrator(self, migrator: Migrator) -> None:
        self.migrator = migrator

    # ------------------------------------------------ GETTERS

    def player(self, slot: int = 0) -> Optional[Asset]:
        players = self._cache.get_instances(AssetInstances.PLAYERS)
        if not players:
            return None
        if slot < len(players):
            return players[slot]
        return players[0]


    def tile(
        self,
        layer: str,
        position: Position,
        instance: str = AssetInstances.ENVIRON
    ) -> Optional[Asset]:
        return self._cache.get_tile(layer, position, instance)


    def character(self, name: str) -> Any:
        return self._cache.get_character(name)


    def characters(self) -> Dict[str, Any]:
        return self._cache.get_characters()


    def asset(self, name: str, layer: Optional[str] = None) -> Optional[Asset]:
        """Retrieves an asset in O(1) by unique name, optionally scoped to a layer."""
        return self._cache.get_asset(name, layer)


    def assets(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        if layer is not None:
            target_assets = self._cache.get_layer_assets(layer)
        else:
            target_assets = self._assets

        if elevation is not None:
            return [a for a in target_assets if a.elevation == elevation]
        return target_assets


    def states(self, layer: str) -> Dict[str, AssetState]:
        """Retrieves an O(1) layer-scoped mapping of asset names to AssetStates."""
        return self._cache.get_states(layer)

    
    def weights(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves physical weight candidates, optionally filtered by layer and elevation."""
        weights = self._cache.get_weights(layer)
        if elevation is not None:
            target_e = max(0, elevation)
            return [w for w in weights if target_e in w.hitbox.elevations(w.properties, w.state)]
        return weights
    

    def dynamics(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves dynamic physical weights (m > 0), optionally filtered by layer and elevation."""
        dynamics = self._cache.get_dynamics(layer)
        if elevation is not None:
            target_e = max(0, elevation)
            return [d for d in dynamics if target_e in d.hitbox.elevations(d.properties, d.state)]
        return dynamics

    def statics(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves static physical weights (m == 0), pre-indexed by normalized elevation."""
        return self._cache.get_statics(layer, elevation)

    def static_version(self, layer: str) -> int:
        """Returns the monotonic static geometry version counter for the specified layer."""
        return self._cache.get_static_version(layer)

    def invalidate_statics(self, layer: Optional[str] = None) -> None:
        """Marks static collider indices dirty and increments the per-layer static version."""
        self._cache.invalidate_statics(layer)

    def obstacles(self, layer: Optional[str] = None, elevation: Optional[int] = None) -> List[Asset]:
        """Retrieves navigational obstacle candidates across one or all layers."""
        obstacles = self._cache.get_obstacles(layer)
        if elevation is not None:
            target_e = max(0, elevation)
            return [o for o in obstacles if target_e in o.hitbox.elevations(o.properties, o.state)]
        return obstacles
    

    def bridges(self, layer: Optional[str] = None) -> List[Asset]:
        """Retrieves static sensor bridge assets for a specific layer or across all layers."""
        return self.instances(AssetInstances.BRIDGES, layer)


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
            return [asset for asset in self._assets if asset.category != AssetCategories.TILES]
        return self._cache.get_renderables(layer)


    def shorelines(self, layer: Optional[str] = None) -> List[Asset]:
        """
        Retrieves active procedural shoreline assets for a specific layer or across all layers.
        """
        if layer is not None:
            return self._cache.get_shorelines(layer)
        return self.instances(AssetInstances.SHORELINES)

    
    def moisture(self, layer: str, x: int, y: int) -> float:
        """
        Queries scalar moisture potential at coordinates (x, y) on the specified layer.
        """
        field = self._moisture_fields.get(layer)
        if not field:
            return 0.0
        return field.evaluate(x, y)


    def size(self, layer: Optional[str] = None) -> List[Dimensions]:
        """Returns cached layer dimensions for a specific layer or all layers."""
        layers = [layer] if layer is not None else self.layers()
        return [self._cache.get_size(l) for l in layers]

    # ------------------------------------------------ MUTATORS

    def set_moisture_field(self, layer: str, field: MoistureField) -> None:
        """
        Stores the compiled MoistureField for the layer and precomputes
        moisture_flux directly on all static ResourceState instances.
        """
        self._moisture_fields[layer] = field
        resources = self.categories(AssetCategories.RESOURCES, layer)
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
        self.loaded = False
        self.paused = False
        self._assets.clear()
        self._cache.clear()
        self.menus.clear()
        self.overlays.clear()
        self.perimeters.clear()
        self._moisture_fields.clear()

    # ------------------------------------------------ EXPORTERS

    def serialize(self, world: str, slot: str) -> None:
        """
        Serializes persistent Board asset states and world metadata into plain
        YAML-safe dictionaries and saves them via Loader.
        """
        dump: Dict[str, Any] = {}

        for asset in self._assets:
            if asset.category in (
                AssetCategories.WIDGETS,
                AssetCategories.GEOGRAPHY
            ):
                continue

            if (
                asset.instance == AssetInstances.DOORS
                and asset.state.projection == LayerProjections.OUT
            ):
                continue

            if asset.category == AssetCategories.EFFECTS:
                if (
                    asset.properties.frequency
                    and asset.properties.frequency.type == Frequencies.TEMPORARY
                    and not asset.properties.frequency.persist
                ):
                    continue

            if asset.category == AssetCategories.SHEETS and asset.instance not in (
                AssetInstances.SPRITES,
                AssetInstances.PLAYERS,
                AssetInstances.PIXIES
            ):
                continue

            cat = str(asset.category)
            inst = str(asset.instance)

            if cat not in dump:
                dump[cat] = {}
            if inst not in dump[cat]:
                dump[cat][inst] = []

            dump[cat][inst].append(serialize(asset.state))

        # Serialize abstract world metadata
        if self.calendar:
            dump[Shortcuts.CALENDAR] = serialize(self.calendar)
        if self.plot:
            dump[Shortcuts.PLOTS] = serialize(self.plot)

        Loader.save_state(world, slot, dump)