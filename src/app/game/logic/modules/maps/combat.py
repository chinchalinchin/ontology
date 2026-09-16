"""
# Ontology: app.game.maps
"""
# Standard Libraries
from typing import List

# Application Libraries
import app.config.settings as settings
from app.models.groups import EquipmentGroup
from app.models.state import (
    SpriteState
)

# Cython Libraries
from libs.core.models import Hitbox

class CombatMap:
    """
    """


    @staticmethod
    def attackboxes(sprite: SpriteState, equipment: EquipmentGroup) -> List[Hitbox]:
        frame_key = settings.SEPARATOR.join([
            sprite.animation.action,
            sprite.animation.direction,
            str(sprite.animation.frame)
        ])
        weapon_key = sprite.inventory.equipment.weapon
        return equipment.weapons.get(weapon_key,{}).attackboxes.get(frame_key)

