"""
# Ontology: app.game.cradle

Package for ingame Asset instantiation.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.hooks.factory import Factory
    
from app.assets.base import Asset
from app.config.enums import AssetInstances, AssetCategories
from app.models.config import RecipeConfiguration
from app.models.groups import SpawnableGroup
from app.models.state import PositionalState, MotorState, PropertyState

class Cradle:
    """
    ## Cradle
    Responsible for creating Asset Instances on the fly during the engine loop.
    """
    recipes: RecipeConfiguration
    spawnables: SpawnableGroup

    def __init__(self, spawnables: SpawnableGroup, recipes: RecipeConfiguration):
        self.spawnables = spawnables
        self.recipes = recipes

    def _generate(self):
        return "TODO"
    
    def spawn_expression(self, id, position, layer):
        recipe = self.recipes.cursors.expressions
        properties = self.spawnables.expressions
        name = self._generate()
        
        state = PositionalState(id=id, name=name, layer=layer, position=position)
        frame = Factory.frame(recipe.frame) if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(id, name, AssetCategories.CURSORS, AssetInstances.EXPRESSIONS)
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_projectile(self, id, position, layer, velocity):
        recipe = self.recipes.cursors.projectiles
        properties = self.spawnables.projectiles
        name = self._generate()
        
        # Instantiate natively
        state = MotorState(
            id=id, name=name, layer=layer, 
            position=position, initial=position, 
            direction="down", speed=10
        )
        # Inject velocity for the physics loop
        state.velocity = velocity 
        
        frame = Factory.frame(recipe.frame) if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(id, name, AssetCategories.CURSORS, AssetInstances.PROJECTILES)
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_temporary(self, id, layer, position):
        recipe = self.recipes.effects.temporary
        properties = self.spawnables.temporary
        name = self._generate()
        
        state = PositionalState(id=id, name=name, layer=layer, position=position)
        frame = Factory.frame(recipe.frame) if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(id, name, AssetCategories.EFFECTS, AssetInstances.TEMPORARY)
        
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_strut(self, id, position, layer, owner):
        recipe = self.recipes.crafts.struts
        properties = self.spawnables.struts  # FIXED: Was .crafts
        name = self._generate()
        
        state = PropertyState(id=id, name=name, layer=layer, position=position, owner=owner)
        frame = Factory.frame(recipe.frame) if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(id, name, AssetCategories.CRAFTS, AssetInstances.STRUTS)
        
        return Asset(taxonomy, properties, state, frame, animation)