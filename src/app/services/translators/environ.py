"""
# Ontology: app.services.translators.environ

Helper functions for ISL conditions.
"""
# Standard Libraries
from typing import Dict, List

# Application Libraries
from app.config.enums import (
    Goals, 
    Intentions, 
    RequiredAssets,
    AssetInstances, 
    AssetCategories,
    Motivations,
    Relationships
)
from app.models.state import (
    SpriteState,
    Goal
)

# Cython Libraries
from libs.core.models import Position

# ----------------------------------------------------- ISL CONDITION CONJUNCTS

def is_near(pos1: Position, pos2: Position, radius: int = 15) -> bool:
    """Fast, pure-Python squared distance check for ISL."""
    if not pos1 or not pos2:
        return False
    dx = pos2.x - pos1.x
    dy = pos2.y - pos1.y
    return (dx*dx + dy*dy) <= (radius * radius)

def any_goals(goals: Dict[Goal], category=None) -> bool:
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
    Evaluates if any goal in memory matches the requested category/categories
    and lies within the specified radius of pos.
    """
    if not sprite.memory.goals or not sprites or not categories:
        return False

    for goal in sprite.memory.goals.values():
        if goal.category not in categories:
            continue

        if goal.name in sprites:
            target = sprites[goal.name]

            if target.layer != sprite.layer:
                continue

            if is_near(
                sprite.position, 
                target.position, 
                sprite.mutators.parameters.vision.radius
            ): return True    

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
        'Intentions': Intentions,
        'Motivations': Motivations,
        'Relationships': Relationships
    }
    functions: dict = {
        'is_near': is_near,
        'any_goals': any_goals,
        'any_memories_visible': any_memories_visible
    }