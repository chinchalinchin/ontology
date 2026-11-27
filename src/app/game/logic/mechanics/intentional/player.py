"""
@domain.concrete
@domain.user
@app.mechanic
@category.sheets
@workflow.player

# Ontology: Source - app.game.logic.mechanics.intentional.player

Player Mechanics for resolving DevicePayload into Player Intention, Goal, and MenuEvent state.
"""
# Standard Libraries
from __future__ import annotations
from typing import (
    Optional,
    TYPE_CHECKING
)
import logging
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board
    from app.game.logic.relations import ProjectileIndex

from app.static.semantics import (
    Actions,
    Intentions,
    PlayerGoals,
    Goals,
    AnimatedIntentions,
    BlockingIntentions,
    Menus,
    Relations
)
from app.game.logic.modules.maps.animation import AnimationMap
from app.game.logic.modules.maps.combat import CombatMap
from app.game.logic.mechanics import Mechanic
from app.models.state import (
    Goal,
    DevicePayload
)
from app.models.menus import (
    InventoryContext,
    PauseContext,
    MenuEvent
)

# Cython Libraries
from libs.core.models import Position

# --------------------------------------------------------------

logger = logging.getLogger(__name__)

_INVENTORY_MENUS = frozenset((
    Menus.EQUIPMENT,
    Menus.POUCH,
    Menus.PACK,
))

# --------------------------------------------------------------


class PlayerMechanics(Mechanic):
    """
    Translates DevicePayload inputs into Player Intentions, Goals, Action
    animations, Equipment admissibility checks, and ranged draw-hold gating.
    """

    @property
    def relation(self) -> Optional[ProjectileIndex]:
        return self.relations.get(Relations.PROJECTILES)

    @relation.setter
    def relation(self, relation: Optional[ProjectileIndex]) -> None:
        if relation is None:
            self.relations.pop(Relations.PROJECTILES, None)
        else:
            self.relations[Relations.PROJECTILES] = relation

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        Updates the Player's Menu events, Intentions, attack charge duration,
        ranged draw-hold gating, movement Goal, and Animation state.
        """
        player = board.player()
        if not player:
            return

        # 1. Intercept Menu Triggers
        if payload.world.menu:
            if payload.world.menu in _INVENTORY_MENUS:
                bus.append(MenuEvent(
                    id=payload.world.menu,
                    context=InventoryContext(
                        inventory=player.state.inventory,
                        slots=player.state.slots
                    )
                ))
                return
            if payload.world.menu == Menus.PAUSE:
                bus.append(MenuEvent(
                    id=Menus.PAUSE,
                    context=PauseContext(board=board)
                ))
                return

        prev_action = player.state.animation.action
        attack_hold = payload.world.holds.get(Intentions.ATTACK, 0)

        # 2. Process Intentions & Grip Parameters
        is_blocking = player.state.intention in BlockingIntentions
        is_animating = player.state.animation.frame > 0 or player.state.animation.tick > 0
        is_locked = is_blocking and is_animating

        intention = payload.world.intention
        if payload.world.grip and not intention:
            intention = Intentions.USE

        # Gate incoming Intention on Equipment admissibility
        if intention and AnimationMap.action(
            player.state,
            board.equipment,
            intention=intention
        ) is None:
            intention = None

        if intention:
            if not is_locked:
                if payload.world.grip and player.state.mutators.parameters:
                    player.state.mutators.parameters.hand = payload.world.grip
                if player.state.intention != intention:
                    player.state.intention = intention
                    player.state.animation.frame = 0
                    player.state.animation.tick = 0
                    if intention == Intentions.ATTACK and player.state.mutators.parameters:
                        player.state.mutators.parameters.charge = attack_hold
        else:
            if not is_locked:
                player.state.intention = Intentions.IDLE

        # Accumulate peak attack hold duration while drawing; reset outside ATTACK
        if player.state.mutators.parameters:
            if player.state.intention == Intentions.ATTACK:
                if attack_hold > 0:
                    player.state.mutators.parameters.charge = max(
                        player.state.mutators.parameters.charge,
                        attack_hold
                    )
            else:
                player.state.mutators.parameters.charge = 0

        # 3. Process Goals / Movement
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y
        has_movement = False

        if PlayerGoals.UP in payload.world.goals:
            goal_y -= speed
            has_movement = True
        if PlayerGoals.DOWN in payload.world.goals:
            goal_y += speed
            has_movement = True
        if PlayerGoals.LEFT in payload.world.goals:
            goal_x -= speed
            has_movement = True
        if PlayerGoals.RIGHT in payload.world.goals:
            goal_x += speed
            has_movement = True

        if has_movement and not player.state.goal:
            player.state.goal = Goal(
                name=player.name,
                category=Goals.POSITION,
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        # Enforce admissibility on active Intention and reset frame/tick on Action change
        action = AnimationMap.action(
            player.state,
            board.equipment
        )
        if action is None:
            player.state.intention = Intentions.IDLE
            action = Actions.WALK
            if player.state.mutators.parameters:
                player.state.mutators.parameters.charge = 0

        player.state.animation.action = action
        if action != prev_action:
            player.state.animation.frame = 0
            player.state.animation.tick = 0

        if player.state.intention in AnimatedIntentions:
            player.state.mutators.triggers.animated = True
        else:
            player.state.mutators.triggers.animated = has_movement

        if player.state.goal and has_movement:
            player.state.animation.direction = AnimationMap.direction(
                player.state.position,
                player.state.goal.position
            )

        # Hold ranged draw pose on (F_release - 1, delay - 1) while attack stays pressed,
        # keeping animated=True so SpriteAnimation never resets the frame to 0.
        if (
            player.state.intention == Intentions.ATTACK
            and attack_hold > 0
            and player.state.animation.frame > 0
            and CombatMap.projectile(player.state, self.relation) is not None
            and CombatMap.release(
                player.state,
                board.equipment,
                player.elevation
            ) is not None
        ):
            delay = CombatMap.delay(player.state, board.equipment)
            player.state.animation.frame -= 1
            player.state.animation.tick = delay - 1

        if player.state.intention == Intentions.ATTACK:
            eq = player.state.slots.equipment
            logger.debug(
                f"SheetState("
                f"id={player.id}"
                f"name={player.name},"
                f"intention={player.state.intention},"
                f"action={player.state.animation.action})"
            )
            logger.debug(
                f"Equipment("
                f"weapon={eq.weapon}, "
                f"armor={eq.armor}, "
                f"shield={eq.shield}, "
                f"tool={eq.tool}, "
                f"utility={eq.utility})"
            )