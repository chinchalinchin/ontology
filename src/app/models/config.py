"""
# Ontology: app.models.configuration

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from typing import Dict, List, Callable
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe,
    StateRecipe,
    Intentions,
    PlayerGoals,
)
from app.models.properties import Action

class Configuration:
    pass

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ CONFIGURATION MODELS
# ---------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ RECIPE CONFIGURATION

@dataclass(slots=True)
class Recipe:
    frame: FrameRecipe = None
    animation: AnimationRecipe = None
    state: StateRecipe = None

@dataclass(slots=True) 
class RecipeConfiguration(Configuration):
    """
    """
    # SHEETS
    pixies: Recipe
    sprites: Recipe
    players: Recipe
    weapons: Recipe
    utilities: Recipe
    armor: Recipe
    tools: Recipe
    # OBJECTS
    chests: Recipe
    crates: Recipe
    doors: Recipe
    gates: Recipe
    plates: Recipe
    # EFFECTS
    temporary: Recipe
    persistent: Recipe
    # CURSORS
    expressions: Recipe
    projectiles: Recipe
    # CRAFTS
    struts: Recipe
    # Tiles
    fore: Recipe
    back: Recipe

# ---------------------------------------------------------------------------------------
# ----------------------------------------------------------------- MAPPING CONFIGURATION

@dataclass(slots=True)
class Mapping:
    intentions: Dict[Intentions, int]
    goals: Dict[PlayerGoals, int]

@dataclass(slots=True)
class MappingConfiguration(Configuration):
    keyboard: Mapping
    controller: Mapping = None

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ ACTION CONFIGURATION

@dataclass(slots=True)
class ActionConfiguration(Configuration):
    """
    """
    id: str
    data: Dict[str, Action]
    
# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------- INTENTION CONFIGURATION

@dataclass(slots=True)
class Transition:
    """
    """
    next: str
    conditions: List[Callable] = field(default_factory=list)

@dataclass(slots=True)
class IntentionConfiguration(Configuration):
    """
    """
    intentions: Dict[str, List[Transition]] = field(default_factory=dict)