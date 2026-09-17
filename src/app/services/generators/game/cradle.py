"""
# Ontology: app.services.generators.cradle

Package for ingame Asset instantiation.
"""
from __future__ import annotations

# Standard Libraries
from typing import TYPE_CHECKING, List
import logging 
import uuid

# Application Libraries
import app.config.settings as settings
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances, 
    AssetCategories
)
from app.services.generators.game.factory import Factory
from app.models.config import RecipeConfiguration
from app.models.groups import SpawnableGroup
from app.models.state import (
    MotorState, 
    PropertyState,
    AttachmentState,
    EffectState,
    HazardState,
    CollectableState,
    ReactableState,
    Damage,
    Lot
)
if TYPE_CHECKING:
    from app.services.generators.game.decomposer import Decomposer
    from app.models.properties import Cost

from libs.core.models import Position, Velocity

logger = logging.getLogger(__name__)

SPAWN = "spawn"

class Cradle:
    """
    ## Cradle
    Responsible for creating Asset Instances on the fly during the engine loop.
    """
    recipes: RecipeConfiguration
    spawnables: SpawnableGroup
    decomposer: 'Decomposer'

    def __init__(self, 
        spawnables: SpawnableGroup, 
        recipes: RecipeConfiguration, 
        decomposer: Decomposer
    ):
        self.spawnables = spawnables
        self.recipes = recipes
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
    ):
        recipe = self.recipes.cursors.projectiles
        properties = self.spawnables.projectiles.get(id)
        name = self.name()
        
        state = MotorState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position, 
            initial     = position, 
            # TODO: determine
            direction   = "down", 
            # TODO: determine
            speed       = 10
        )
        # Inject velocity for the physics loop
        state.velocity = velocity 
        
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id = id, 
            name = name, 
            category = AssetCategories.CURSORS, 
            instance = AssetInstances.PROJECTILES
        )
        
        return Asset(taxonomy, properties, state, frame, animation)


    def spawn_collectable(self, 
        id: str, 
        layer: str, 
        position: Position,
        lot: Lot
    ) -> Asset:
        recipe = self.recipes.effects.collectables
        properties = self.spawnables.collectables.get(id)
        name = self.name()

        state = CollectableState(
            id=id,
            name=name,
            layer=layer,
            position=position,
            lot=lot
        )
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id=id,
            name=name,
            category=AssetCategories.EFFECTS,
            instance=AssetInstances.COLLECTABLES
        )
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_hazard(self, 
        id: str, 
        layer: str, 
        position: Position,
        damage: Damage
    ) -> Asset:
        recipe = self.recipes.effects.hazards
        properties = self.spawnables.hazards.get(id)
        name = self.name()

        state = HazardState(
            id=id,
            name=name,
            layer=layer,
            position=position,
            damage=damage
        )
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id=id,
            name=name,
            category=AssetCategories.EFFECTS,
            instance=AssetInstances.HAZARDS
        )
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_strut(self, 
        id: str, 
        position: Position,  # type: ignore
        layer: str, 
        owner: str
    ):
        recipe = self.recipes.crafts.struts
        properties = self.spawnables.struts.get(id)
        name = self.name()
        
        state = PropertyState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position, 
            owner       = owner
        )
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id          = id, 
            name        = name, 
            category    = AssetCategories.CRAFTS, 
            instance    = AssetInstances.STRUTS
        )
        
        return Asset(taxonomy, properties, state, frame, animation)


    def spawn_composition(self, 
        id: str, 
        position: Position,  # type: ignore
        layer: str, 
        owner: str
    ) -> List[Asset]:
        """
        Dynamically spawn an entire composition schema through the engine's mechanics flow.
        """
        name = self.name()
        pseudo_state    = PropertyState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position, 
            owner       = owner
        )
        return self.decomposer.unpack(pseudo_state)


    def cost(self, id: str) -> List[Cost]:
        """
        Delegates compositional cost aggregation to the Decomposer tree traverse utilities.
        """
        return self.decomposer.cost(id)