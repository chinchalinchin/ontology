"""
@domain.logic
@app.module
@workflow.projectiles

# Ontology: Source - app.game.logic.relations.projectiles

Relational index mapping Projectiles and Weapons.
"""
# Standard Libraries
import logging

# Application Libraries
from app.assets.base import Singleton

logger = logging.getLogger(__name__)

# TODO


class ProjectileIndex(Singleton):
    """
    Compiled relational index for Projectile and Weapon spaces.
    """

    def from_properties(self):
        pass
