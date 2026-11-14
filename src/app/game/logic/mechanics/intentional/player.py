"""
@domain.concrete
@domain.user
@app.mechanic
@category.sheets
@modality.intention
@workflow.player

# Ontology: Source - app.game.logic.mechanics.intentional.player

Player Mechanics for resolving DevicePayload into Player Intention, Goal, and MenuEvent state.
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import collections

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.static.semantics import (
    Intentions,
    PlayerGoals,
    Goals,
    AnimatedIntentions,
    BlockingIntentions,
    Menus
)
from app.game.logic.modules.maps.animation import AnimationMap
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
    Menus.EQUIPMENT.value,
    Menus.POUCH.value,
    Menus.PACK.value,
))

# --------------------------------------------------------------

class PlayerMechanics(Mechanic):

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
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
            if payload.world.menu == Menus.PAUSE.value:
                bus.append(MenuEvent(
                    id=Menus.PAUSE.value,
                    context=PauseContext(board=board)
                ))
                return

        # 2. Process Intentions & Grip Parameters
        is_blocking = player.state.intention in BlockingIntentions
        is_animating = player.state.animation.frame > 0 or player.state.animation.tick > 0
        is_locked = is_blocking and is_animating

        intention = payload.world.intention
        if payload.world.grip and not intention:
            intention = Intentions.USE.value

        if intention:
            if not is_locked:
                if payload.world.grip:
                    player.state.mutators.parameters.hand = payload.world.grip
                if player.state.intention != intention:
                    player.state.intention = intention
                    player.state.animation.frame = 0
                    player.state.animation.tick = 0
        else:
            if not is_locked:
                player.state.intention = Intentions.IDLE.value
        
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
                category=Goals.POSITION.value, 
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        if player.state.intention in AnimatedIntentions:
            player.state.mutators.triggers.animated = True
        else:
            player.state.mutators.triggers.animated = has_movement

        player.state.animation.action = AnimationMap.action(
            player.state, 
            board.equipment
        )

        if player.state.goal and has_movement:
            player.state.animation.direction = AnimationMap.direction(
                player.state.position,
                player.state.goal.position
            )

        if player.state.intention == Intentions.ATTACK.value:
            eq = player.state.slots.equipment
            logger.info(
                f"SheetState("
                f"id={player.id}"
                f"name={player.name},"
                f"intention={player.state.intention},"
                f"action={player.state.animation.action})"
            )
            logger.info(
                f"Equipment("
                f"weapon={eq.weapon}, "
                f"armor={eq.armor}, "
                f"shield={eq.shield}, "
                f"tool={eq.tool}, "
                f"utility={eq.utility})"
            )