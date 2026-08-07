"""
# Ontology: Factory
"""
from typing import get_type_hints, Type, TypeVar, Any

from app.assets.animations import (
    BinaryAnimation, PersistentAnimation, TemporaryAnimation, StateAnimation
)
from app.assets.frames import (
    SingleFrame, IterableFrame, StateFrame
)
from app.models.recipes import FrameRecipe, AnimationRecipe, StateRecipe
from app.models.state import (
    AnimatorState, ContainerState, DoorState, SwitchState, 
    MetricState, MultiplierState, PositionalState, PropertyState,
    PixieState, SpriteState
)
from app.models.properties import (
    EffectProperties, CursorProperties, ObjectProperties, 
    TileProperties, PixieProperties, SpriteProperties, StrutProperties
)

T = TypeVar('T')

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
        StateRecipe.PIXIE: PixieState,
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
        "tiles": TileProperties,
        "effects": EffectProperties,
        "objects": ObjectProperties,
        "cursors": CursorProperties,
        "struts": StrutProperties,
        "sheets": SpriteProperties 
    }

    @staticmethod
    def _hydrate(cls: Type[T], data: dict[str, Any]) -> T:
        if not isinstance(data, dict): return data
        hints = get_type_hints(cls)
        hydrated_data = {}
        for key, value in data.items():
            expected_type = hints.get(key)
            if isinstance(value, dict) and hasattr(expected_type, '__annotations__'):
                hydrated_data[key] = Factory._hydrate(expected_type, value)
            else:
                hydrated_data[key] = value
        return cls(**hydrated_data)

    @staticmethod
    def state(recipe: StateRecipe, snapshot: dict) -> Any:
        target_cls = Factory.STATE_MAP.get(recipe)
        if not target_cls:
            raise ValueError(f"Unknown state recipe type: {recipe}")
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def properties(category: str, snapshot: dict) -> Any:
        # Edge case handling for Pixies vs Sprites inside the 'sheets' category
        if category == "sheets" and snapshot.get("entities"):
            target_cls = PixieProperties
        else:
            target_cls = Factory.PROPERTY_MAP.get(category)
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def frame(recipe: FrameRecipe):
        return Factory.FRAME_MAP.get(recipe, SingleFrame)()

    @staticmethod
    def animation(recipe: AnimationRecipe):
        return Factory.ANIMATION_MAP.get(recipe, PersistentAnimation)()