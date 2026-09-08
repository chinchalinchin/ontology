"""
# Ontology: app.game.logic.mechanics.intentional.social
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import collections
import logging

if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    Intentions, 
    AssetInstances, 
    Goals, 
    Expressions,
    ExpressionsPalette,
    Menus
)
from app.game.logic.mechanics.spatial.base import SpatialMechanic
from app.game.menus.contexts import DialogueContext
from app.game.menus.events import MenuEvent
from app.models.state import DevicePayload
from libs.core.models import Position

logger = logging.getLogger(__name__)

class SocialMechanics(SpatialMechanic):
    """
    ## SocialMechanics

    Mechanic responsible for governing entity-to-entity interactions, including 
    Player-initiated dialogue and NPC-to-NPC rumor passing.
    """
    def __init__(self):
        super().__init__(max_entities=1000)

    def update(self, 
        board: Board, 
        delta: float, 
        bus: collections.deque, 
        payload: DevicePayload
    ) -> None:
        
        processed_sources = set()

        for layer in board.layers():
            players = board.instances(AssetInstances.PLAYERS.value, layer)
            sprites = board.instances(AssetInstances.SPRITES.value, layer)

            # -------------------------------------------------------------
            # PHASE 1: PLAYER-TO-NPC INTERACTION (Spatial Resolution)
            # -------------------------------------------------------------
            interacting_players = [
                p for p in players 
                if p.state.intention == Intentions.INTERACT.value
                and p.name not in processed_sources
            ]

            if len(interacting_players) > 0:
                names = [ p.name for p in interacting_players ]
                logger.info(f"Processing Player Interactions for: {names}")
                logger.info(f"Possible Sprite Interactions: {len(sprites)}")

            if interacting_players and sprites:
                logger.info('Checking collisions')
                colliding_pairs = self.proximities(interacting_players + sprites)

                if len(colliding_pairs) > 0:
                    names = [ (a[0].name, a[1].name ) for a in colliding_pairs ]
                    logger.info(f"Processing Interaction Collisions: {names}")

                for asset_a, asset_b in colliding_pairs:
                    is_a_player = asset_a in interacting_players
                    is_b_sprite = asset_b in sprites
                    is_b_player = asset_b in interacting_players
                    is_a_sprite = asset_a in sprites

                    if is_a_player and is_b_sprite:
                        player, npc = asset_a, asset_b
                    elif is_b_player and is_a_sprite:
                        player, npc = asset_b, asset_a
                    else:
                        continue

                    if player.name in processed_sources:
                        continue

                    logger.info(f"processing: {npc.state.psyche.dialogue}")

                    # 1. Trigger Dialogue Menu
                    if npc.state.psyche.dialogue:
                        bus.append(MenuEvent(
                            id=Menus.DIALOGUE.value,
                            context=DialogueContext(
                                plot=board.plot,
                                sprite=npc.state
                            )
                        ))

                    processed_sources.add(player.name)

            # -------------------------------------------------------------
            # PHASE 2: NPC-TO-NPC & EXPRESSION SPAWNING (Logical Resolution)
            # -------------------------------------------------------------
            for sprite in sprites:
                if sprite.state.intention in [
                    Intentions.SPEAK.value, 
                    Intentions.BARTER.value, 
                    Intentions.THREATEN.value
                ]:
                    # Check lock: Only fire data transfer if expression doesn't exist
                    if not sprite.state.psyche.expression:
                        goal = sprite.state.goal

                        if goal and goal.category == Goals.SUBJECT.value:

                            target = board.asset(goal.name, sprite.state.layer)
                            
                            if target:
                                # NPC-to-NPC Rumor passing
                                if target.instance == AssetInstances.SPRITES.value:
                                    if sprite.state.psyche.dialogue:
                                        target.state.memory.rumors.append(sprite.state.psyche.dialogue)
                                        sprite.state.psyche.dialogue = None

                                # Spawns LOQUACITY for BOTH NPC-to-NPC and Player-to-NPC
                                sprite.state.psyche.expression = board.cradle.spawn_expression(
                                    ExpressionsPalette.BUBBLES.value, 
                                    Expressions.LOQUACITY.value, 
                                    sprite
                                )