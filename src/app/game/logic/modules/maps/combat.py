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
from app.models.state import SheetState

# Cython Libraries
from libs.core.models import Hitbox

class CombatMap:
    """
    """

    @staticmethod
    def attackboxes(
        state: SheetState,
        equipment: EquipmentGroup,
        elevation: Optional[int] = None
    ) -> List[Hitbox]:
        weapon_key = state.slots.equipment.weapon
        weapon = equipment.weapons.get(weapon_key) if weapon_key else None
        if not weapon or not weapon.hitbox:
            return []
        resolved_elevation = (
            elevation if elevation is not None
            else (state.elevation if state.elevation is not None else 0)
        )
        return weapon.hitbox.get(weapon.properties, state, resolved_elevation)