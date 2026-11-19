"""
@domain.logic
@app.module
@workflow.combat

# Ontology: Source - app.game.maps.combat

CombatMaps for mapping SpriteState Frame keys to Equipment Attackboxes,
projectile relations, release coordinates, and launch speeds.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    List,
    Optional,
    Tuple,
    TYPE_CHECKING
)

# Application Libraries
import app.static.settings as settings
from app.models.groups import EquipmentGroup
from app.models.state import SheetState

if TYPE_CHECKING:
    from app.game.logic.relations import ProjectileIndex

# Cython Libraries
from libs.core.models import (
    Hitbox,
    Position
)


class CombatMap:
    """
    Stateless projections from active Combat/Animation states, Equipment,
    and ProjectileIndex into Combat Resolution artifacts.
    """

    @staticmethod
    def projectile(
        state: SheetState,
        relation: Optional[ProjectileIndex]
    ) -> Optional[str]:
        """
        Resolves the projectile Asset ID emitted by the attacker's equipped weapon.
        """
        if not relation or not state.slots:
            return None
        weapon_key = state.slots.equipment.weapon
        if not weapon_key:
            return None
        return relation.resolve(weapon_key)

    @staticmethod
    def attackboxes(
        state: SheetState,
        equipment: EquipmentGroup,
        elevation: Optional[int] = None
    ) -> List[Hitbox]:
        """
        Resolves active melee AttackHitbox primitives for the current animation frame.
        """
        if not state.slots:
            return []
        weapon_key = state.slots.equipment.weapon
        weapon = equipment.weapons.get(weapon_key) if weapon_key else None
        if not weapon or not weapon.hitbox:
            return []
        resolved_elevation = (
            elevation if elevation is not None
            else (state.elevation if state.elevation is not None else 0)
        )
        return weapon.hitbox.get(weapon.properties, state, resolved_elevation)

    @staticmethod
    def release(
        state: SheetState,
        equipment: EquipmentGroup,
        elevation: Optional[int] = None
    ) -> Optional[Tuple[Position, str]]:
        """
        Pulls the weapon's active AttackHitbox on the frame entry tick (tick == 1),
        returning the world-space spawn center and launch direction.
        """
        if state.animation.tick != 1:
            return None

        hitboxes = CombatMap.attackboxes(state, equipment, elevation)
        if not hitboxes:
            return None

        hb = hitboxes[0]
        spawn_x = state.position.x + hb.position.x + (hb.dimensions.w // 2)
        spawn_y = state.position.y + hb.position.y + (hb.dimensions.l // 2)
        return (Position(spawn_x, spawn_y), state.animation.direction)

    @staticmethod
    def speed(
        state: SheetState,
        equipment: EquipmentGroup
    ) -> int:
        """
        Computes charged scalar launch speed s(S, n) = round(alpha * S * (1 + tau(n))),
        where tau(n) = min(1.0, n / max(1, frame * delay)).
        """
        strength = state.character.strength if state.character else 10
        charge = max(0, state.mutators.parameters.charge) if state.mutators.parameters else 0

        delay = 1
        if state.slots and state.slots.equipment.weapon:
            weapon = equipment.weapons.get(state.slots.equipment.weapon)
            if weapon and isinstance(weapon.properties.actions, dict):
                action_prop = weapon.properties.actions.get(state.animation.action)
                if action_prop:
                    delay = max(1, action_prop.delay)

        n_max = max(1, state.animation.frame * delay)
        tau = min(1.0, charge / n_max)
        alpha = settings.PROJECTILE_BASE_SPEED_FACTOR

        return max(1, round(alpha * strength * (1.0 + tau)))