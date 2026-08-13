"""
# Ontology: app.hooks.factory

Package for instantiating Asset classes and their components.
"""
# Standard Libraries
from typing import get_type_hints, get_origin, get_args, Union
import types

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
    AssetCategories,
    Devices,
    Mechanics
)
from app.game.mechanics import (
    AnimationMechanics,
    CollisionMechanics, 
    ProjectileMechanics,
    SwitchMechanics, 
    MotionMechanics,
    CommerceMechanics,
    TransitionMechanics,
    PlayerMechanics,
    RemoveMechanics
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
    SpriteState,
    PlayerState
)
from app.models.properties import (
    EffectProperties,
    CursorProperties, 
    ObjectProperties, 
    TileProperties, 
    CraftProperties, 
    SheetProperties,
    EquipmentProperties,
    IntentionProperties
)
from app.game.devices import (
    Keyboard,
    Controller
)

# Cython Libraries
from libs.core.models import (
    Position, 
    Dimensions, 
    Hitbox, 
    AttackBox
)

class Factory:
    CYTHON_HINTS = {
        Hitbox: {'position': Position, 'dimensions': Dimensions},
        AttackBox: {'position': Position, 'dimensions': Dimensions, 'hitframe': int}
    }
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
        StateRecipe.SPRITE: SpriteState,
        StateRecipe.PLAYER: PlayerState
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

    DEVICE_MAP = {
        Devices.KEYBOARD: Keyboard,
        Devices.CONTROLLER: Controller
    }

    MECHANICS_MAP = {
        Mechanics.ANIMATION: AnimationMechanics,
        Mechanics.COLLISION: CollisionMechanics,
        Mechanics.PROJECTILE: ProjectileMechanics,
        Mechanics.SWITCH: SwitchMechanics,
        Mechanics.COMMERCE: CommerceMechanics,
        Mechanics.TRANSITION: TransitionMechanics,
        Mechanics.PLAYER: PlayerMechanics,
        Mechanics.REMOVE: RemoveMechanics
    }

    @classmethod
    def _hydrate(cls, target_cls, data):
        """
        Recursively instantiate dataclasses and Cython structs from dictionaries.
        """
        if not isinstance(data, dict):
            return data

        # Extract type hints, failing gracefully for Cython extension types
        try:
            hints = get_type_hints(target_cls)
        except (TypeError, AttributeError):
            hints = {}

        if not hints:
            hints = cls.CYTHON_HINTS.get(target_cls, {})

        kwargs = {}
        for key, value in data.items():
            if value is None or key not in hints:
                kwargs[key] = value
                continue

            field_type = hints[key]
            origin = get_origin(field_type)

            # Resolve Optional/Union types
            if origin is Union or origin is getattr(types, 'UnionType', type(None)):
                args = get_args(field_type)
                field_type = next((t for t in args if t is not type(None)), field_type)
                origin = get_origin(field_type)

            # Recursively apply instantiation 
            if origin is list and isinstance(value, list):
                inner_type = get_args(field_type)[0]
                kwargs[key] = [cls._hydrate(inner_type, item) for item in value]
            elif origin is dict and isinstance(value, dict):
                inner_type = get_args(field_type)[1]
                kwargs[key] = {k: cls._hydrate(inner_type, v) for k, v in value.items()}
            elif isinstance(value, dict) and isinstance(field_type, type):
                kwargs[key] = cls._hydrate(field_type, value)
            else:
                kwargs[key] = value

        return target_cls(**kwargs)
    
    @staticmethod
    def state(recipe: StateRecipe, snapshot: dict):
        target_cls = Factory.STATE_MAP.get(recipe)
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def properties(category: str, snapshot: dict):
        target_cls = Factory.PROPERTY_MAP.get(category)
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def frame(recipe: FrameRecipe):
        return Factory.FRAME_MAP.get(recipe, SingleFrame)()

    @staticmethod
    def animation(recipe: AnimationRecipe):
        return Factory.ANIMATION_MAP.get(recipe, PersistentAnimation)()

    @staticmethod
    def taxonomy(category, instance, id, name):
        return Taxonomy(
            id          = id,
            name        = name,
            instance    = instance,
            category    = category,
        )

    @staticmethod
    def equipment(snapshot):
        return Factory._hydrate(EquipmentProperties, snapshot)

    @staticmethod
    def intentions(snapshot):
        return Factory._hydrate(IntentionProperties, snapshot)

    @staticmethod
    def device(dev, mapping):
        target_cls = Factory.DEVICE_MAP.get(dev)
        return Factory._hydrate(target_cls, mapping)

    @staticmethod 
    def mechanic(kind):
        return Factory.MECHANICS_MAP.get(kind)()
