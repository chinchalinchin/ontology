"""
# Ontology: app.services.factory

Package for instantiating Asset classes and their components.
"""
from typing import Any

# Application Libraries
from app.assets.animations import (
    BinaryAnimation, 
    PersistentAnimation, 
    TemporaryAnimation, 
    StateAnimation,
    TraversalAnimation,
    MeterAnimation,
    NoAnimation
)
from app.assets.base import Taxonomy
from app.assets.frames import (
    SingleFrame, 
    IterableFrame, 
    StateFrame,
    SpriteFrame,
    TraversalFrame,
    MeterFrame,
    IndexFrame,
    NoFrame
)
from app.config.enums import (
    AnimationRecipe, 
    FrameRecipe, 
    Devices,
    Mechanics,
    Controllers
)
from app.game.logic.mechanics import (
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
    SpeechMechanics,
    InteractionMechanics,
    MenuMechanics,
    CognitionMechanics
)
from app.game.menus.controllers import (
    DisplayController,
    ScrollController
)
from app.models.config import (
    RecipeConfiguration,
)
from app.models.groups import SpawnableGroup
from app.game.devices import (
    Keyboard,
    Controller
)

class Factory:
    FRAME_MAP = {
        FrameRecipe.SPRITE: SpriteFrame,
        FrameRecipe.SINGLE: SingleFrame,
        FrameRecipe.ITERABLE: IterableFrame,
        FrameRecipe.STATE: StateFrame,
        FrameRecipe.TRAVERSAL: TraversalFrame,
        FrameRecipe.METER: MeterFrame,
        FrameRecipe.INDEX: IndexFrame,
        FrameRecipe.NONE: NoFrame
    }

    ANIMATION_MAP = {
        AnimationRecipe.BINARY: BinaryAnimation,
        AnimationRecipe.PERSISTENT: PersistentAnimation,
        AnimationRecipe.TEMPORARY: TemporaryAnimation,
        AnimationRecipe.STATE: StateAnimation,
        AnimationRecipe.TRAVERSAL: TraversalAnimation,
        AnimationRecipe.METER: MeterAnimation,
        AnimationRecipe.NONE: NoAnimation
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
        Mechanics.INTERACTION: InteractionMechanics,
        Mechanics.PLAYER: PlayerMechanics,
        Mechanics.REMOVE: RemoveMechanics,
        Mechanics.COMBAT: CombatMechanics,
        Mechanics.MOTION: MotionMechanics,
        Mechanics.SPEECH: SpeechMechanics,
        Mechanics.MENU: MenuMechanics
    }

    CONTROLLER_MAP  = {
        Controllers.DISPLAY: DisplayController,
        Controllers.SCROLL: ScrollController
    }

    @staticmethod
    def frame(recipe: Any):
        if isinstance(recipe, str):
            for enum_key, frame_cls in Factory.FRAME_MAP.items():
                if enum_key.value == recipe:
                    return frame_cls()
        return Factory.FRAME_MAP.get(recipe, SingleFrame)()

    @staticmethod
    def animation(recipe: Any):
        if isinstance(recipe, str):
            for enum_key, anim_cls in Factory.ANIMATION_MAP.items():
                if enum_key.value == recipe:
                    return anim_cls()
        return Factory.ANIMATION_MAP.get(recipe, PersistentAnimation)()
    
    @staticmethod
    def taxonomy(id: str, name: str, category: str, instance: str):
        return Taxonomy(id, name, category, instance)

    @staticmethod
    def device(dev: str, mapping: dict):
        target_cls = Factory.DEVICE_MAP.get(dev, Keyboard)
        return target_cls(mapping)

    @staticmethod
    def cradle(spawnables: SpawnableGroup, recipes: RecipeConfiguration, decomposer: Any):
        from app.services.generators.cradle import Cradle
        return Cradle(spawnables, recipes, decomposer)

    @staticmethod 
    def mechanics(kind: Any):
        if isinstance(kind, str):
            for enum_key, cls in Factory.MECHANICS_MAP.items():
                if enum_key.value == kind:
                    return cls()
        return Factory.MECHANICS_MAP.get(kind, AnimationMechanics)()

    @staticmethod
    def controller(kind: Any):
        if isinstance(kind, str):
            for enum_key, cls in Factory.CONTROLLER_MAP.items():
                if enum_key.value == kind:
                    return cls()
        return Factory.CONTROLLER_MAP.get(kind, ScrollController)()