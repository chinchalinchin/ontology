"""
# Ontology: app.hooks.factory

Package for instantiating Asset classes and their components.
"""
from typing import Any

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
    Devices,
    Mechanics
)
from app.hooks.cradle import Cradle
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
    InteractionMechanics
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
        FrameRecipe.NONE: NoFrame
    }

    ANIMATION_MAP = {
        AnimationRecipe.BINARY: BinaryAnimation,
        AnimationRecipe.PERSISTENT: PersistentAnimation,
        AnimationRecipe.TEMPORARY: TemporaryAnimation,
        AnimationRecipe.STATE: StateAnimation,
        AnimationRecipe.NONE: NoAnimation,
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
        Mechanics.SPEECH: SpeechMechanics
    }

    @staticmethod
    def frame(recipe: FrameRecipe):
        return Factory.FRAME_MAP.get(recipe, SingleFrame)()

    @staticmethod
    def animation(recipe: AnimationRecipe):
        return Factory.ANIMATION_MAP.get(recipe, PersistentAnimation)()

    @staticmethod
    def taxonomy(id: str, name: str, category: str, instance: str):
        return Taxonomy(id, name, category, instance)

    @staticmethod
    def device(dev: str, mapping: dict):
        target_cls = Factory.DEVICE_MAP.get(dev, Keyboard)
        return target_cls(mapping)

    @staticmethod 
    def mechanics(kind: str):
        return Factory.MECHANICS_MAP.get(kind, AnimationMechanics)()

    @staticmethod
    def cradle(spawnables: SpawnableGroup, recipes: RecipeConfiguration, decomposer: Any):
        return Cradle(spawnables, recipes, decomposer)