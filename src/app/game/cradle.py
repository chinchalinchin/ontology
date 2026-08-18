
"""
# Ontology: app.game.cradle

Package for ingame Asset instantiation.
"""
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances,
    AssetCategories
)
from app.hooks.factory import Factory
from app.models.config import RecipeConfiguration
from app.models.groups import SpawnableGroup

class Cradle:
    """
    ## Cradle

    The Cradle class is the "live" Factory. It is responsible for creating Asset Instances on the fly for the engine and mechanics, while the game loop is engaged.
    """
    recipes: RecipeConfiguration
    spawnables: SpawnableGroup

    def __init__(self, spawnables: SpawnableGroup, recipes: RecipeConfiguration):
        self.spawnables = spawnables
        self.recipes = recipes

    def _generate(self):
        """
        Returns a unique name for each spawned instance.
        """
        return "TODO"
    
    def spawn_expression(self, id, position):
        """
        """
        recipe = self.recipes.cursors.expressions
        properties = self.spawnables.cursors
        name = self._generate()
        state = Factory.state(recipe.state, {
            'position': position,
        })
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id, 
            name,
            AssetCategories.CURSORS, 
            AssetInstances.EXPRESSIONS
        )
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_projectile(self, id, position, direction, speed):
        """
        """
        recipe = self.recipes.cursors.projectiles
        properties = self.spawnables.projectiles
        name = self._generate()
        state = Factory.state(recipe.state, {
            'position': position,
            'initial': position, 
            'direction': direction, 
            'speed': speed
        })
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id, 
            name,
            AssetCategories.CURSORS, 
            AssetInstances.PROJECTILES
        )
        return Asset(taxonomy, properties, state, frame, animation)


    def spawn_temporary(self, id, position):
        """
        """
        recipe = self.recipes.effects.temporary
        properties = self.spawnables.temporary
        name = self._generate()
        state = Factory.state(recipe.state, {
            'position': position,
        })
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id, 
            name,
            AssetCategories.EFFECTS, 
            AssetInstances.TEMPORARY
        )
        return Asset(taxonomy, properties, state, frame, animation)

    def spawn_strut(self, id, position, owner):
        """
        """
        recipe = self.recipes.crafts.struts
        properties = self.spawnables.crafts
        name = self._generate()
        state = Factory.state(recipe.state, {
            'position': position,
            'owner': owner
        })
        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            id, 
            name,
            AssetCategories.CRAFTS, 
            AssetInstances.STRUTS
        )
        return Asset(taxonomy, properties, state, frame, animation)