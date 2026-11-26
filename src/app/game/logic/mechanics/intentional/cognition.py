"""
@domain.concrete
@domain.logic
@app.mechanic
@modality.intention
@workflow.cognition

# Ontology: Source - app.game.logic.mechanics.intentional.cognition

CognitionMechanics implementation. Manages Sprite Goals via a four-stage
cognitive pipeline: Sense -> Resolve -> Acquire (IDLE-only) -> Sync.
"""
from __future__ import annotations

# Standard Libraries
import collections
import logging
from typing import (
    Any,
    Optional,
    Sequence,
    Tuple,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from app.game.board import Board

# Application Libraries
from app.assets.base import Asset
from app.game.logic.mechanics import Mechanic
from app.game.logic.modules.cognition import (
    ConverseInstinct,
    FleeInstinct,
    GoalResolver,
    HostilityInstinct,
    Instinct,
    Perception,
    Recall,
    WanderInstinct
)
from app.models.state import DevicePayload
from app.services.automaton import GoalEvaluator
from app.static.semantics import (
    AssetInstances,
    Executors,
    Goals,
    Intentions,
    Outcomes
)

# -----------------------------------------------------

logger = logging.getLogger(__name__)

# -----------------------------------------------------


class CognitionMechanics(Mechanic):
    """
    ## CognitionMechanics

    Deliberative cognitive pipeline managing Sprite Goals across four stages
    per tick:
      1. Sense: Perception scan, fear evaluation, and active Goal tracking.
      2. Resolve: Survival preemption or declarative GoalResolver classification.
      3. Acquire (IDLE-only): Survival -> Recall (stack -> goals) -> Drives -> Explore.
      4. Sync: Post-resolution / post-acquisition visibility and layer subsumption.
    """
    perception: Perception
    recall: Recall
    resolver: Optional[GoalResolver]
    survival: Tuple[Instinct, ...]
    drives: Tuple[Instinct, ...]
    exploratory: Tuple[Instinct, ...]

    def __init__(
        self,
        perception: Optional[Perception] = None,
        recall: Optional[Recall] = None,
        resolver: Optional[GoalResolver] = None,
        survival: Optional[Sequence[Instinct]] = None,
        drives: Optional[Sequence[Instinct]] = None,
        exploratory: Optional[Sequence[Instinct]] = None
    ):
        super().__init__()
        self.perception = perception if perception is not None else Perception()
        self.recall = recall if recall is not None else Recall()
        self.resolver = resolver
        self.survival = (
            tuple(survival) if survival is not None
            else (FleeInstinct(),)
        )
        self.drives = (
            tuple(drives) if drives is not None
            else (HostilityInstinct(), ConverseInstinct())
        )
        self.exploratory = (
            tuple(exploratory) if exploratory is not None
            else (WanderInstinct(),)
        )

    def set_executor(self, key: str, executor: Any) -> None:
        """Registers an Executor and binds GoalResolver for Executors.GOAL."""
        super().set_executor(key, executor)
        if key == Executors.GOAL:
            self.resolver = (
                GoalResolver(evaluator=executor)
                if executor is not None
                else None
            )

    @property
    def executor(self) -> Optional[GoalEvaluator]:
        """Typed GoalEvaluator bound to Executors.GOAL."""
        return self.executors.get(Executors.GOAL)

    @executor.setter
    def executor(self, executor: Optional[GoalEvaluator]) -> None:
        if executor is None:
            self.executors.pop(Executors.GOAL, None)
            self.resolver = None
        else:
            self.executors[Executors.GOAL] = executor
            self.resolver = GoalResolver(evaluator=executor)

    @staticmethod
    def log_goal(
        sprite: Asset,
        verb: str = "transformed",
        level: int = logging.INFO
    ) -> None:
        """Logs the Sprite's current active Goal at the specified log level."""
        goal = sprite.state.goal
        if goal is None:
            return
        logger.log(
            level,
            f"{sprite.name} {verb} Goal("
            f"category={goal.category}, "
            f"name={goal.name}, "
            f"layer={goal.layer}, "
            f"position=({goal.position.x}, {goal.position.y}))"
        )

    def _sense(self, sprite: Asset, board: Board) -> None:
        """
        Stage 1 (Sense): Scans same-layer environment, updates fear trigger,
        and tracks active Goal coordinates without cross-layer telepathy.
        """
        self.perception.scan(sprite, board)
        self.perception.fear(sprite, board)
        self.perception.track(sprite, board)

    def _resolve(self, sprite: Asset, board: Board) -> bool:
        """
        Stage 2 (Resolve): Applies Survival preemption when frightened outside
        ESCAPE, or evaluates the compiled Goal Resolution Matrix via GoalResolver.
        Returns True if sprite.state.goal changed during resolution.
        """
        goal = sprite.state.goal
        if goal is None:
            return False

        # Survival preemption: shelf non-transient active Goals non-dormant
        # without emitting a confusion reflex so TransitionMechanics exits to IDLE
        is_escape_goal = (
            goal.category == Goals.POSITION
            and goal.name == Intentions.ESCAPE.value
        )
        if (
            sprite.state.mutators.triggers.frightened
            and sprite.state.intention != Intentions.ESCAPE
            and not is_escape_goal
        ):
            if (
                goal.category not in (Goals.POSITION, Goals.DOOR)
                and goal.name
            ):
                goal.dormant = False
                sprite.state.memory.goals[goal.name] = goal
            sprite.state.goal = None
            logger.info(
                f"{sprite.name} preempted Goal("
                f"category={goal.category}, name={goal.name}) due to fear"
            )
            return True

        if self.resolver is None:
            return False

        was_stalled = sprite.state.trajectory.stalled
        outcome = self.resolver.resolve(sprite, board)
        if outcome is None:
            return False

        if (
            outcome == Outcomes.LOST
            and goal.category == Goals.DOOR
            and goal.name
            and was_stalled
        ):
            self.perception.mark_stalled_door(
                sprite_name=sprite.name,
                layer=goal.layer or sprite.state.layer,
                door_name=goal.name
            )

        return sprite.state.goal is not goal

    def _acquire(self, sprite: Asset, board: Board) -> bool:
        """
        Stage 3 (Acquire): Executes strictly when intention == IDLE and
        goal is None, selecting the first Goal across five monotonic tiers:
          1. Survival Instincts
          2. Commitment Stack (Recall: memory.stack LIFO)
          3. Episodic Memory (Recall: non-dormant memory.goals)
          4. Drive Instincts
          5. Exploratory Instincts
        """
        if (
            sprite.state.intention != Intentions.IDLE
            or sprite.state.goal is not None
        ):
            return False

        # Tier 1: Survival Instincts
        for instinct in self.survival:
            goal = instinct.generate(sprite, board)
            if goal is not None:
                sprite.state.goal = goal
                self.log_goal(sprite, verb="acquired")
                return True

        # Tiers 2 & 3: Commitment Stack (LIFO) -> Episodic Memory
        recalled = self.recall.remember(sprite, board)
        if recalled is not None:
            sprite.state.goal = recalled
            return True

        # Tier 4: Drive Instincts
        for instinct in self.drives:
            goal = instinct.generate(sprite, board)
            if goal is not None:
                sprite.state.goal = goal
                self.log_goal(sprite, verb="acquired")
                return True

        # Tier 5: Exploratory Instincts
        for instinct in self.exploratory:
            goal = instinct.generate(sprite, board)
            if goal is not None:
                sprite.state.goal = goal
                self.log_goal(sprite, verb="acquired")
                return True

        return False

    def _sync(
        self,
        sprite: Asset,
        board: Board,
        resolved_changed: bool,
        acquired: bool
    ) -> None:
        """
        Stage 4 (Sync): Refreshes Perception.track whenever Stage 2 or Stage 3
        changed the active Goal, and validates newly acquired Stage 3 Goals via
        GoalResolver so cross-layer Door subsumption completes on the same tick.
        """
        if not (resolved_changed or acquired):
            return

        if sprite.state.goal is None:
            sprite.state.mutators.triggers.vision = False
            return

        self.perception.track(sprite, board)

        if acquired and self.resolver is not None:
            previous_goal = sprite.state.goal
            outcome = self.resolver.resolve(sprite, board)
            if outcome is not None and sprite.state.goal is not previous_goal:
                if sprite.state.goal is not None:
                    self.perception.track(sprite, board)
                else:
                    sprite.state.mutators.triggers.vision = False

    def update(
        self,
        board: Board,
        delta: float,
        bus: collections.deque,
        payload: DevicePayload
    ) -> None:
        """
        ### update(board: Board, delta: float, bus: collections.deque, payload: DevicePayload)

        Mechanic interface for receiving information from the Engine.
        """
        player = board.player()
        player_name = player.name if player is not None else None

        for sprite in board.instances(AssetInstances.SPRITES):
            # Skip the player (B074 safe guard when board.player() is None)
            if player_name is not None and sprite.name == player_name:
                continue

            if sprite.state.mutators.triggers.dead:
                continue

            # Stage 1: Sense
            self._sense(sprite, board)
            # Stage 2: Resolve
            resolved_changed = self._resolve(sprite, board)
            # Stage 3: Acquire (IDLE only)
            acquired = self._acquire(sprite, board)
            # Stage 4: Sync
            self._sync(sprite, board, resolved_changed, acquired)