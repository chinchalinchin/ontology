"""
@domain.system
@app.services
@workflow.injection

# Ontology: Source - app.services.generators.game.cradle

Package for ingame Asset instantiation.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    TYPE_CHECKING, 
    List,
    Union,
)
import logging 
import uuid

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances, 
    AssetCategories,
    Orientations,
    Directions,
    # ---------
    Ceramics,
    Chromatics,
    Geologics,
    Metallics,
    Organics,
    # ---------
    Buildings,
    Corridors,
    Columns,
    Enclosures,
    Inclines,
)
from app.game.logic.relations import MaterialIndex
from app.services.factories.assets import AssetFactory
from app.models.config import RecipeConfiguration
from app.models.groups import SpawnableGroup
from app.models.state import (
    AnimationState,
    CraftState,
    MotorState, 
    PropertyState,
    AttachmentState,
    EffectState,
    HazardState,
    CollectableState,
    ShorelineState,
    Damage,
    Lot
)

if TYPE_CHECKING:
    from app.services.generators.game.decomposer import Decomposer

from libs.core.models import (
    Hitbox,
    Position, 
    Velocity,
    Multiple
)

logger = logging.getLogger(__name__)

SPAWN = "spawn"


class Cradle:
    """
    ## Cradle
    Responsible for creating Asset Instances on the fly during the engine loop.
    """
    recipes: RecipeConfiguration
    spawnables: SpawnableGroup
    decomposer: Decomposer
    materials: MaterialIndex

    def __init__(self, 
        spawnables: SpawnableGroup, 
        recipes: RecipeConfiguration, 
        materials: MaterialIndex,
        decomposer: Decomposer
    ):
        self.spawnables = spawnables
        self.recipes = recipes
        self.materials = materials
        self.decomposer = decomposer


    @staticmethod
    def name() -> str:
        return settings.SEPARATOR.join([ SPAWN, uuid.uuid4().hex[:8] ])

    
    def spawn_expression(self, 
        id: str, 
        icon: str, 
        target: Asset
    ) -> AttachmentState:
        properties = self.spawnables.expressions.get(id)
        
        # Calculate top-right anchor using properties and target dimensions
        if properties and target.dimensions:
            ox = target.dimensions.w - 2*properties.dimensions.w
            # TODO: parameterize or shift to properties
            oy = -0.9*properties.dimensions.l
        else:
            ox, oy = 0, 0
            
        return AttachmentState(
            id=id,
            layer=target.state.layer,
            icon=icon, 
            offset=Position(x=ox, y=oy),
            ttl=settings.EXPRESSION_TTL
        )


    def spawn_projectile(self, 
        id: str, 
        position: Position,  # type: ignore
        layer: str, 
        velocity: Velocity # type: ignore
    ) -> Asset:
        name = self.name()
        state = MotorState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position, 
            initial     = position, 
            # TODO: determine
            direction   = Directions.DOWN.value, 
            # TODO: determine
            speed       = 10
        )
        # Inject velocity for the physics loop
        state.velocity = velocity 

        return AssetFactory.asset(
            category=AssetCategories.CURSORS.value,
            instance=AssetInstances.PROJECTILES.value,
            properties=self.spawnables.projectiles.get(id),
            state=state,
            recipe=self.recipes.cursors.projectiles,
            substrate=self.materials.substrate(AssetInstances.PROJECTILES.value)
        )


    def spawn_collectable(self, 
        id: str, 
        layer: str, 
        position: Position,
        lot: Lot
    ) -> Asset:
        state = CollectableState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            lot=lot
        )
        return AssetFactory.asset(
            category=AssetCategories.EFFECTS.value,
            instance=AssetInstances.COLLECTABLES.value,
            properties=self.spawnables.collectables.get(id),
            state=state,
            recipe=self.recipes.effects.collectables,
            substrate=self.materials.substrate(AssetInstances.COLLECTABLES.value)
        )


    def spawn_hazard(self, 
        id: str, 
        layer: str, 
        position: Position,
        damage: Damage
    ) -> Asset:
        state = HazardState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            damage=damage
        )
        return AssetFactory.asset(
            category=AssetCategories.EFFECTS.value,
            instance=AssetInstances.HAZARDS.value,
            properties=self.spawnables.hazards.get(id),
            state=state,
            recipe=self.recipes.effects.hazards,
            substrate=self.materials.substrate(AssetInstances.HAZARDS.value)
        )


    def spawn_passive(self, id: str, layer: str, position: Position) -> Asset:
        state = EffectState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            animation=AnimationState()
        )
        return AssetFactory.asset(
            category=AssetCategories.EFFECTS.value,
            instance=AssetInstances.PASSIVE.value,
            properties=self.spawnables.passive.get(id),
            state=state,
            recipe=self.recipes.effects.passive,
            substrate=self.materials.substrate(AssetInstances.PASSIVE.value)
        )


    def spawn_shoreline(self,
        id: str,
        layer: str,
        position: Position,
        orientation: str,
        length: int,
        hitboxes: List[Hitbox],  # type: ignore
    ) -> Asset:
        properties = self.spawnables.shorelines.get(id)

        state = ShorelineState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            orientation=orientation,
            length=length,
            hitboxes=hitboxes
        )
        return AssetFactory.asset(
            category=AssetCategories.GEOGRAPHY.value,
            instance=AssetInstances.SHORELINES.value,
            properties=properties,
            state=state,
            recipe=self.recipes.geography.shorelines,
            substrate=self.materials.substrate(AssetInstances.SHORELINES.value)
        )


    def spawn_composition(self, 
        id: str, 
        position: Position,  # type: ignore,
        material: Union[Ceramics,Chromatics,Geologics,Metallics,Organics],
        blueprint: Union[Buildings,Corridors,Columns,Enclosures,Orientations,Inclines,Directions],
        layer: str, 
        owner: str
    ) -> List[Asset]:
        """
        Dynamically spawn an entire composition schema through the engine's mechanics flow.
        """
        pseudo_state = PropertyState(
            id          = id, 
            name        = self.name(), 
            layer       = layer, 
            position    = position, 
            owner       = owner
        )
        return self.decomposer.unpack(pseudo_state)


    def spawn_bridge(
        self,
        id: str,
        layer: str,
        position: Position,
        material: Union[Geologics,Metallics,Organics],
        blueprint: Orientations,
        multiple: Multiple
    ) -> List[Asset]:
        """
        Spawns and unpacks a bridge configuration via Decomposer.
        """
        bridge_state = CraftState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            material=material,
            blueprint=blueprint,
            multiple=multiple
        )
        return self.decomposer.multiply(
            bridge_state,
            AssetCategories.CRAFTS.value,
            AssetInstances.BRIDGES.value
        )