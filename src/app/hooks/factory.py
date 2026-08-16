"""
# Ontology: app.hooks.factory

Package for instantiating Asset classes and their components.
"""
# Standard Libraries
from typing import get_type_hints, get_origin, get_args, Union, List, Dict
import types

# Application Libraries
from app.assets.animations import (
    BinaryAnimation, 
    PersistentAnimation, 
    TemporaryAnimation, 
    StateAnimation,
    NoAnimation
)
from app.assets.base import Taxonomy
from app.assets.frames import (
    SingleFrame, 
    IterableFrame, 
    StateFrame,
    SpriteFrame,
    NoFrame
)
from app.config.enums import (
    AnimationRecipe, 
    FrameRecipe, 
    StateRecipe,
    AssetCategories,
    Devices,
    Mechanics,
    Configurations,
    Groups
)
from app.game.mechanics import (
    AnimationMechanics,
    CollisionMechanics, 
    ProjectileMechanics,
    SwitchMechanics, 
    MotionMechanics,
    CombatMechanics,
    CommerceMechanics,
    TransitionMechanics,
    PlayerMechanics,
    RemoveMechanics,
    SpeechMechanics
)
from app.models.config import (
    RecipeConfiguration,
    MappingConfiguration,
    IntentionConfiguration,
    ActionConfiguration,
    Mapping
)
from app.models.state import (
    AnimatorState, 
    ContainerState, 
    DoorState, 
    SwitchState, 
    MetricState, 
    MultiplierState,
    NoState, 
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
    SheetProperties
)
from app.models.groups import (
    EquipmentGroup,
    ConfigurationGroup
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
)

class Factory:
    CYTHON_HINTS = {
        Hitbox: {'position': Position, 'dimensions': Dimensions},
    }

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
        StateRecipe.PLAYER: PlayerState,
        StateRecipe.NONE: NoState
    }

    FRAME_MAP = {
        FrameRecipe.SPRITE: SpriteFrame,
        FrameRecipe.SINGLE: SingleFrame,
        FrameRecipe.ITERABLE: IterableFrame,
        FrameRecipe.STATE: StateFrame,
        FrameRecipe.NONE: NoFrame
    }

    ANIMATION_MAP = {
        AnimationRecipe.BINARY: BinaryAnimation,
        AnimationRecipe.PERSISTENT: PersistentAnimation,
        AnimationRecipe.TEMPORARY: TemporaryAnimation,
        AnimationRecipe.STATE: StateAnimation,
        AnimationRecipe.NONE: NoAnimation,
    }

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
        Mechanics.REMOVE: RemoveMechanics,
        Mechanics.COMBAT: CombatMechanics,
        Mechanics.MOTION: MotionMechanics,
        Mechanics.SPEECH: SpeechMechanics
    }

    CONFIGURATION_MAP = {
        Configurations.ACTIONS: ActionConfiguration,
        Configurations.INTENTIONS: IntentionConfiguration,
        Configurations.RECIPES: RecipeConfiguration,
        Configurations.MAPPINGS: MappingConfiguration
    }

    GROUP_MAP = {
        Groups.EQUIPMENT: EquipmentGroup,
        Groups.CONFIGURATIONS: ConfigurationGroup
    }

    @classmethod
    def _hydrate(cls, target_cls, data):
        """
        Recursively instantiate dataclasses and Cython structs from dictionaries.
        """
        origin = get_origin(target_cls)

        # Handle native collection types seamlessly
        if origin is list and isinstance(data, list):
            inner_type = get_args(target_cls)[0]
            return [cls._hydrate(inner_type, item) for item in data]
            
        if origin is dict and isinstance(data, dict):
            inner_type = get_args(target_cls)[1]
            return {k: cls._hydrate(inner_type, v) for k, v in data.items()}

        if target_cls is dict or target_cls is list:
            return data

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
            field_origin = get_origin(field_type)

            # Resolve Optional/Union types
            if field_origin is Union or field_origin is getattr(types, 'UnionType', type(None)):
                args = get_args(field_type)
                field_type = next((t for t in args if t is not type(None)), field_type)

            kwargs[key] = cls._hydrate(field_type, value)

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
    def configuration(config, snapshot):
        target_cls = Factory.CONFIGURATION_MAP.get(config)
        return Factory._hydrate(target_cls, snapshot)

    @staticmethod
    def group(grouping, snapshot):
        target_cls = Factory.GROUP_MAP.get(grouping)
        return Factory._hydrate(target_cls, snapshot)
    
    @staticmethod
    def frame(recipe: FrameRecipe):
        return Factory.FRAME_MAP.get(recipe, SingleFrame)()

    @staticmethod
    def animation(recipe: AnimationRecipe):
        return Factory.ANIMATION_MAP.get(recipe, PersistentAnimation)()

    @staticmethod
    def taxonomy(id, name, category, instance,):
        return Taxonomy(id, name, category, instance)

    @staticmethod
    def device(dev, mapping):
        target_cls = Factory.DEVICE_MAP.get(dev, Keyboard)
        mapping_obj = Factory._hydrate(Mapping, mapping)
        return target_cls(mapping_obj)

    @staticmethod 
    def mechanics(kind):
        return Factory.MECHANICS_MAP.get(kind, AnimationMechanics)()
