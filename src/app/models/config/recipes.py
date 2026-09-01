"""
# Ontology: app.models.config.recipes

Models for typing the configuration attributes of Asset Recipes. 
"""
# Standard Libraries

from dataclasses import dataclass

# Application Libraries
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe,
    StateRecipe,
)
from app.models.config.core import Configuration


# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------ RECIPE CONFIGURATION

@dataclass(slots=True)
class Recipe:
    frame: FrameRecipe = None
    animation: AnimationRecipe = None
    state: StateRecipe = None

@dataclass(slots=True)
class TileRecipe:
    fore: Recipe = None
    back: Recipe = None

@dataclass(slots=True)
class CraftRecipe:
    struts: Recipe = None

@dataclass(slots=True)
class CursorRecipe:
    expressions: Recipe = None
    projectiles: Recipe = None

@dataclass(slots=True)
class EffectRecipe:
    temporary: Recipe = None
    persistent: Recipe = None

@dataclass(slots=True)
class ObjectRecipe:
    chests: Recipe = None
    crates: Recipe = None
    doors: Recipe = None
    gates: Recipe = None
    plates: Recipe = None

@dataclass(slots=True)
class SheetRecipe:
    pixies: Recipe = None
    sprites: Recipe = None
    players: Recipe = None
    weapons: Recipe = None
    utilities: Recipe = None
    armor: Recipe = None
    tools: Recipe = None
    shields: Recipe = None

@dataclass(slots=True)
class WidgetRecipe:
    buttons: Recipe = None
    icons: Recipe = None
    meters: Recipe = None
    pages: Recipe = None
    panes: Recipe = None
    
@dataclass(slots=True) 
class RecipeConfiguration(Configuration):
    """
    """
    tiles: TileRecipe = None
    crafts: CraftRecipe = None
    cursors: CursorRecipe = None
    effects: EffectRecipe = None
    objects: ObjectRecipe = None
    sheets: SheetRecipe = None
    widgets: WidgetRecipe = None