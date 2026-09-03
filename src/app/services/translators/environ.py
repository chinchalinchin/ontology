"""
# Ontology: app.services.translators.environ

Helper functions for ISL conditions.
"""
# Application Libraries
from app.config.enums import (
    Goals, 
    Intentions, 
    AssetInstances, 
    AssetCategories,
    Motivations
)

# ----------------------------------------------------- ISL CONDITION CONJUNCTS

def is_near(pos1, pos2, radius: int = 15) -> bool:
    """Fast, pure-Python squared distance check for ISL."""
    if not pos1 or not pos2:
        return False
    dx = pos2.x - pos1.x
    dy = pos2.y - pos1.y
    return (dx*dx + dy*dy) <= (radius * radius)

# ----------------------------------------------------------------------------

class Environ:
    constants: dict = {
        #### Asset Space Enumerations
        'AssetInstances': AssetInstances,
        'AssetCategories': AssetCategories,
        #### Intention Space Enumerations
        'Goals': Goals,
        'Intentions': Intentions,
        'Motivations': Motivations
    }
    functions: dict = {
        'is_near': is_near
    }