"""
# Ontology: app.services.translators.environ

Helper functions for ISL conditions.
"""
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

# ----------------------------------------------------- ISL CONDITION CONJUNCTS

def is_near(pos1, pos2, radius: int = 15) -> bool:
    """Fast, pure-Python squared distance check for ISL."""
    if not pos1 or not pos2:
        return False
    dx = pos2.x - pos1.x
    dy = pos2.y - pos1.y
    return (dx*dx + dy*dy) <= (radius * radius)

def check_memory(goals, category=None) -> bool:
    if not goals: 
        return False
    if category:
        return any(g.category == category for g in goals.values())
    return True

# ----------------------------------------------------------------------------

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
        'check_memory': check_memory
    }