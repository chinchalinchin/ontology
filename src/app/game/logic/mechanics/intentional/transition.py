"""
@domain.automata
@domain.concrete
@domain.logic
@app.mechanic
@category.sheets
@modality.intention
@workflow.transitions

# Ontology: Source - app.game.logic.mechanics.intentional.transition

TransitionMechanics implementation.
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import collections
import logging

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.static.semantics import (
    Actions,
    StaticIntentions,
    AssetInstances,
    Intentions,
    Executors
)
from app.game.logic.modules.maps import AnimationMap
from app.game.logic.mechanics import Mechanic
from app.models.state import DevicePayload
from app.services.automaton import TransitionExecutor

# --------------------------------------------------------------

logger = logging.getLogger(__name__)

# --------------------------------------------------------------


class TransitionMechanics(Mechanic):
    """
    Evaluates Intention transition criteria and resolves the Sprite's intended
    goals to animation Actions and spatial Directions.
    """

    @property
    def executor(self) -> Optional[TransitionExecutor]:
        return self.executors.get(Executors.INTENTION)

    @executor.setter
    def executor(self, executor: Optional[TransitionExecutor]) -> None:
        if executor is None:
            self.executors.pop(Executors.INTENTION, None)
        else:
            self.executors[Executors.INTENTION] = executor

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        sprites = board.instances(AssetInstances.SPRITES)
        sprites_dict = board.characters()
        player = board.player()

        for sprite in sprites:
            prev_action = sprite.state.animation.action

            # 1. Evaluate State ISL Conditions
            if self.executor and sprite.state.intention:
                next_intent = self.executor.evaluate(
                    current_state=sprite.state.intention,
                    locals={
                        'sprite': sprite.state,
                        'sprites': sprites_dict,
                        'assets': board.states(sprite.state.layer),
                    }
                )
                current_intent = sprite.state.intention

                if next_intent and next_intent != current_intent:
                    # Gate candidate transition on Equipment admissibility
                    if AnimationMap.action(
                        sprite.state,
                        board.equipment,
                        intention=next_intent
                    ) is not None:
                        logger.info(
                            f"Transition({sprite.name}): "
                            f"{sprite.state.intention} -> "
                            f"{next_intent}"
                        )
                        sprite.state.intention = next_intent
                    else:
                        logger.debug(
                            f"Transition({sprite.name}) rejected: "
                            f"{current_intent} -> {next_intent} (inadmissible equipment)"
                        )

            # 2. Resolve Action (revert inadmissible active states to IDLE / WALK)
            action = AnimationMap.action(
                sprite.state,
                board.equipment
            )
            if action is None:
                logger.debug(
                    f"Transition({sprite.name}): Reverting inadmissible active "
                    f"intention '{sprite.state.intention}' to IDLE."
                )
                sprite.state.intention = Intentions.IDLE
                action = Actions.WALK

            sprite.state.animation.action = action
            if action != prev_action:
                sprite.state.animation.frame = 0
                sprite.state.animation.tick = 1

            # 3. Resolve Direction
            target_pos = sprite.state.trajectory.target or (
                sprite.state.goal.position if sprite.state.goal else None
            )

            if target_pos:
                sprite.state.animation.direction = AnimationMap.direction(
                    sprite.state.position,
                    target_pos
                )

            # 4. Update Animation Trigger
            if not player or sprite.name != player.name:
                # Animate if doing an action OR if moving towards a goal
                is_active_intention = sprite.state.intention not in StaticIntentions
                has_active_velocity = (
                    sprite.state.velocity.vx != 0
                    or sprite.state.velocity.vy != 0
                )

                sprite.state.mutators.triggers.animated = (
                    is_active_intention or has_active_velocity
                )