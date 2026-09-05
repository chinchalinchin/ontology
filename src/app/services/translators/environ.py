"""
# Ontology: app.services.translators.environ

Helper functions for ISL conditions.
"""
# Standard Libraries
from typing import List

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
from app.models.state import Goal

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

def check_goals(goals: List[Goal], category=None) -> bool:
    if not goals: 
        return False
    if category:
        return any(g.category == category for g in goals.values())
    return True

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
        'check_goals': check_goals
    }