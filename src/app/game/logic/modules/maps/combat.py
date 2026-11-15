"""
@domain.logic
@app.module
@workflow.combat

# Ontology: Source - app.game.maps.combat

CombatMaps for mapping SpriteState Frame keys to Equipment Attackboxes.
"""
# Standard Libraries
from typing import (
    List,
    Optional
)

# Application Libraries
from app.models.groups import EquipmentGroup
from app.models.state import SpriteState
from app.assets.hitboxes import AttackHitbox

# Cython Libraries
from libs.core.models import Hitbox

class CombatMap:
    """
    """

    @staticmethod
    def attackboxes(
        state: SpriteState,
        equipment: EquipmentGroup,
        elevation: Optional[int] = None
    ) -> List[Hitbox]:
        weapon_key = state.inventory.equipment.weapon
        weapon_props = equipment.weapons.get(weapon_key) if weapon_key else None
        if not weapon_props:
            return []
        resolved_elevation = (
            elevation if elevation is not None
            else (state.elevation if state.elevation is not None else 0)
        )
        return AttackHitbox().get(weapon_props, state, resolved_elevation)
