"""
# Ontology: Factory

Package for instantiating Asset classes and their components.
"""
# Application Libraries
from app.assets.animations import (
    BinaryAnimation, 
    PersistentAnimation, 
    TemporaryAnimation, 
    StateAnimation
)
from app.assets.base import Taxonomy
from app.assets.frames import (
    SingleFrame, 
    IterableFrame, 
    StateFrame
)
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe, 
    StateRecipe,
    AssetCategories
)
from app.models.state import (
    AnimatorState, 
    ContainerState, 
    DoorState, 
    SwitchState, 
    MetricState, 
    MultiplierState, 
    PositionalState, 
    PropertyState,
    SpriteState
)
from app.models.properties import (
    EffectProperties,
    CursorProperties, 
    ObjectProperties, 
    TileProperties, 
    CraftProperties, 
    SheetProperties
)

class Factory:
    
    # Map Enums directly to Runtime Data Classes
    STATE_MAP = {
        StateRecipe.MULTIPLIER: MultiplierState,
        StateRecipe.POSITIONAL: PositionalState,
        StateRecipe.METRIC: MetricState,
        StateRecipe.ANIMATOR: AnimatorState,
        StateRecipe.CONTAINER: ContainerState,
        StateRecipe.DOOR: DoorState,
        StateRecipe.SWITCH: SwitchState,
        StateRecipe.PROPERTY: PropertyState,
        StateRecipe.SPRITE: SpriteState
    }

    FRAME_MAP = {
        FrameRecipe.SINGLE: SingleFrame,
        FrameRecipe.ITERABLE: IterableFrame,
        FrameRecipe.STATE: StateFrame
    }

    ANIMATION_MAP = {
        AnimationRecipe.BINARY: BinaryAnimation,
        AnimationRecipe.PERSISTENT: PersistentAnimation,
        AnimationRecipe.TEMPORARY: TemporaryAnimation,
        AnimationRecipe.STATE: StateAnimation
    }

    # Properties are strictly grouped by their broad categories
    PROPERTY_MAP = {
        AssetCategories.TILES: TileProperties,
        AssetCategories.EFFECTS: EffectProperties,
        AssetCategories.OBJECTS: ObjectProperties,
        AssetCategories.CURSORS: CursorProperties,
        AssetCategories.CRAFTS: CraftProperties,
        AssetCategories.SHEETS: SheetProperties 
    }

    @staticmethod
    def state(recipe: StateRecipe, snapshot: dict):
        cls = Factory.STATE_MAP.get(recipe)
        return cls(**snapshot)

    @staticmethod
    def properties(category: str, snapshot: dict):
        cls = Factory.PROPERTY_MAP.get(category)
        return cls(**snapshot)

    @staticmethod
    def frame(recipe: FrameRecipe):
        return Factory.FRAME_MAP.get(recipe, SingleFrame)()

    @staticmethod
    def animation(recipe: AnimationRecipe):
        return Factory.ANIMATION_MAP.get(recipe, PersistentAnimation)()

    @staticmethod
    def taxonomy(category, instance, snapshot):
        return Taxonomy(
            id = snapshot.id,
            name = snapshot.name,
            category = category,
            instance = instance
        )
                    