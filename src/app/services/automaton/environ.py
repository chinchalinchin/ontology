"""
@domain.automata
@domain.logic
@app.service

# Ontology: Source - app.services.translators.environ

Helper functions for Transition and Goal Resolution conditions.
"""
# Standard Libraries
from types import SimpleNamespace
from typing import (
    Any,
    Dict,
    List,
    Optional
)

# Application Libraries
from app.static.semantics import (
    RequiredAssets,
    AssetInstances,
    AssetCategories,
    # -------------
    Goals,
    Outcomes,
    Responses,
    Reflexes,
    Intentions,
    Motivations,
    Relationships,
    # --------------
    Seasons,
    Cycles,
    Lifespans,
    AnnualStages,
    PerennialStages,
    CentennialStages
)
from app.models.state import (
    SpriteState,
    Goal
)

# Cython Libraries
from libs.core.models import Position

# ----------------------------------------------------- ISL CONDITION CONJUNCTS


def is_near(pos1: Position, pos2: Position, radius: int = 15) -> bool:
    """Fast, pure-Python inclusive closed-ball squared distance check for ISL."""
    if not pos1 or not pos2 or radius < 0:
        return False
    dx = pos2.x - pos1.x
    dy = pos2.y - pos1.y
    return (dx * dx + dy * dy) <= (radius * radius)


def any_goals(goals: Dict[str, Goal], category: Optional[str] = None) -> bool:
    """Evaluates whether episodic goal memory contains any matching goal."""
    if not goals:
        return False
    if category:
        return any(g.category == category for g in goals.values())
    return len(goals) > 0


def any_memories_visible(
    sprite: SpriteState,
    sprites: Dict[str, SpriteState],
    categories: List[str]
) -> bool:
    """
    Evaluates if any goal in memory matches the requested category/categories,
    refers to a living same-layer character, and lies within the sprite's
    vision radius.
    """
    if not sprite.memory.goals or not sprites or not categories:
        return False

    vision_radius = sprite.mutators.parameters.vision.radius

    for goal in sprite.memory.goals.values():
        if goal.category not in categories:
            continue

        target = sprites.get(goal.name)
        if target is None:
            continue

        if target.layer != sprite.layer:
            continue

        if target.mutators.triggers.dead:
            continue

        if is_near(
            sprite.position,
            target.position,
            vision_radius
        ):
            return True

    return False


# -------------------------------------------------- ISL EXECUTION ENVIRONMENT


class Environ:
    constants: dict = {
        #### Asset Space Enumerations
        'AssetInstances': AssetInstances,
        'AssetCategories': AssetCategories,
        'RequiredAssets': RequiredAssets,
        #### Intention Space Enumerations
        'Goals': Goals,
        'Outcomes': Outcomes,
        'Responses': Responses,
        'Reflexes': Reflexes,
        'Intentions': Intentions,
        'Motivations': Motivations,
        'Relationships': Relationships,
        #### Seasonality Space Enumerations
        'Seasons': Seasons,
        'Cycles': Cycles,
        'Lifespans': Lifespans,
        'AnnualStages': AnnualStages,
        'PerennialStages': PerennialStages,
        'CentennialStages': CentennialStages
    }
    functions: dict = {
        'is_near': is_near,
        'any_goals': any_goals,
        'any_memories_visible': any_memories_visible
    }

    @classmethod
    def globals(cls) -> Dict[str, Any]:
        """Constructs the shared ISL global namespace for condition backends."""
        return {
            'constants': SimpleNamespace(**cls.constants),
            'functions': SimpleNamespace(**cls.functions)
        }