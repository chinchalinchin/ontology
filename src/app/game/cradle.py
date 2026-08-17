
"""
# Ontology: app.game.cradle

Package for ingame Asset instantiation.
"""

from app.models.config import RecipeConfiguration

class Cradle:
    """
    """
    recipes: RecipeConfiguration
    # TODO: Make into POPO.
    properties: dict

    def __init__(self, properties, recipes):
        self.properties = properties
        self.recipes = recipes

    def spawn_expression(self, id, position):
        """
        """
        pass

    def spawn_projectile(id, position, direction, speed):
        """
        """
        pass

    def spawn_temporary(id, position):
        """
        """
        pass

    def spawn_start(id, position, owner):
        """
        """
        pass