"""
# Ontology: Factory
"""
# Standard Libraries
from typing import get_type_hints, Type, TypeVar, Any

# Application Libraries
from app.assets.animations import (
    BinaryAnimation, PersistentAnimation, TemporaryAnimation,
    StateAnimation
)
from app.assets.frames import (
    SingleFrame, IterableFrame, StateFrame
)
from app.models.state import (
    AnimatorState, ContainerState, DoorState, SwitchState, 
    MetricState, MultiplierState, PositionalState, PropertyState,
    PixieState, SpriteState
)
from app.models.properties import (
    EffectProperties, CursorProperties, ObjectProperties, 
    TileProperties, PixieProperties, SpriteProperties,
    StrutProperties
)

T = TypeVar('T')

class Factory:

    @staticmethod
    def _hydrate(cls: Type[T], data: dict[str, Any]) -> T:
        """
        Recursively converts a dictionary into the target dataclass `cls`
        by inspecting its type hints.
        """
        if not isinstance(data, dict):
            return data

        # Get the type annotations for the target class
        hints = get_type_hints(cls)
        hydrated_data = {}

        for key, value in data.items():
            expected_type = hints.get(key)
            
            # If the expected type is a class itself (and the value is a dict),
            # recursively hydrate it. E.g., Position, AnimationState, Mutator
            if isinstance(value, dict) and hasattr(expected_type, '__annotations__'):
                hydrated_data[key] = Factory._hydrate(expected_type, value)
            else:
                hydrated_data[key] = value

        return cls(**hydrated_data)

    @staticmethod
    def state(instance: str, snapshot: dict) -> Any:
        # Map the instance string directly to the target Class
        type_map = {
            "multiplier": MultiplierState,
            "positional": PositionalState,
            "metric": MetricState,
            "animator": AnimatorState,
            "container": ContainerState,
            "door": DoorState,
            "switch": SwitchState,
            "property": PropertyState,
            "pixie": PixieState,
            "sprite": SpriteState
        }
        
        target_cls = type_map.get(instance)
        if not target_cls:
            raise ValueError(f"Unknown state instance type: {instance}")
            
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def properties(category: str, snapshot: dict) -> Any:
        type_map = {
            "tiles": TileProperties,
            "effects": EffectProperties,
            "objects": ObjectProperties,
            "cursors": CursorProperties,
            "pixies": PixieProperties,
            "sprites": SpriteProperties,
            "struts": StrutProperties
        }
        
        target_cls = type_map.get(category)
        if not target_cls:
            raise ValueError(f"Unknown property category: {category}")
            
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def frame(recipe):
        if recipe.frame == "single":
            return SingleFrame()
        if recipe.frame == "iterable":
            return IterableFrame
        if recipe.frame == "state":
            return StateFrame()
        return SingleFrame()

    @staticmethod
    def animation(recipe):
        if recipe.animation == "binary":
            return BinaryAnimation()
        if recipe.animation == "persistent":
            return PersistentAnimation()
        if recipe.animation == "temporary":
            return TemporaryAnimation()
        if recipe.animation == "state":
            return StateAnimation()
        return PersistentAnimation()
