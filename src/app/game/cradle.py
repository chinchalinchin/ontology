"""
# Ontology: app.game.cradle

Package for ingame Asset instantiation.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List

# Application Libraries
if TYPE_CHECKING:
    from app.hooks.factory import Factory
    from app.hooks.decomposer import Decomposer
    from app.models.properties import Cost
    
from app.assets.base import Asset
from app.config.enums import AssetInstances, AssetCategories
from app.models.config import RecipeConfiguration
from app.models.groups import SpawnableGroup
from app.models.state import (
    PositionalState, 
    MotorState, 
    PropertyState
)
from app.models.adapters import (
    PydanticVelocity as Velocity, 
    PydanticPosition as Position
)

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

    def _generate(self):
        return "TODO"
    
    def spawn_expression(self, 
        id: str, 
        position: Position, 
        layer: str
    ):
        recipe = self.recipes.cursors.expressions
        properties = self.spawnables.expressions
        name = self._generate()
        
        state = PositionalState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position
        )
        frame = Factory.frame(recipe.frame) \
                    if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                    if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(
            id          = id, 
            name        = name, 
            category    = AssetCategories.CURSORS, 
            instance    = AssetInstances.EXPRESSIONS
        )
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_projectile(self, 
        id: str, 
        position: Position, 
        layer: str, 
        velocity: Velocity
    ):
        recipe = self.recipes.cursors.projectiles
        properties = self.spawnables.projectiles
        name = self._generate()
        
        # Instantiate natively
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
        
        frame = Factory.frame(recipe.frame) \
                    if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                    if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(
            id = id, 
            name = name, 
            category = AssetCategories.CURSORS, 
            instance = AssetInstances.PROJECTILES
        )
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_temporary(self, 
        id: str, 
        layer: str, 
        position: Position
    ):
        recipe = self.recipes.effects.temporary
        properties = self.spawnables.temporary
        name = self._generate()
        
        state = PositionalState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position
        )
        frame = Factory.frame(recipe.frame) \
                    if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                    if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(
            id          = id, 
            name        = name, 
            category    = AssetCategories.EFFECTS, 
            instance    = AssetInstances.TEMPORARY
        )
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_strut(self, 
        id: str, 
        position: Position, 
        layer: str, 
        owner: str
    ):
        recipe = self.recipes.crafts.struts
        properties = self.spawnables.struts 
        name = self._generate()
        
        state = PropertyState(
            id          = id, 
            name        = name, 
            layer       = layer, 
            position    = position, 
            owner       = owner
        )
        frame = Factory.frame(recipe.frame) \
                    if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                    if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(
            id          = id, 
            name        = name, 
            category    = AssetCategories.CRAFTS, 
            instance    = AssetInstances.STRUTS
        )
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_composition(self, 
        id: str, 
        position: Position, 
        layer: str, 
        owner: str
    ) -> List[Asset]:
        """
        Dynamically spawn an entire composition schema through the engine's mechanics flow.
        """
        pseudo_state = PropertyState(id=id, name="runtime", layer=layer, position=position, owner=owner)
        return self.decomposer.unpack(pseudo_state)

    def cost(self, id: str) -> List['Cost']:
        """
        Delegates compositional cost aggregation to the Decomposer tree traverse utilities.
        """
        return self.decomposer.cost(id)