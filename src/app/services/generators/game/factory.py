"""
# Ontology: app.services.orchestration.factory

Package for instantiating Asset classes and their components.
"""
# Standard Libraries
from typing import Any, Dict

# Application Libraries
from app.assets.animations import (
    BinaryAnimation, 
    LifecycleAnimation,
    StateAnimation,
    SpriteAnimation,
    TraversalAnimation,
    MeterAnimation,
    NoAnimation
)
from app.assets.base import (
    Taxonomy,
    Frame,
    Animation
)
from app.assets.frames import (
    SingleFrame, 
    IterableFrame, 
    StateFrame,
    SpriteFrame,
    FluidFrame,
    ShorelineFrame,
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
    Controllers,
    Translators
)
from app.game.logic.mechanics import (
    AnimationMechanics,
    CollisionMechanics, 
    ProjectileMechanics,
    SwitchMechanics, 
    MotionMechanics,
    CombatMechanics,
    TransitionMechanics,
    PlayerMechanics,
    RemoveMechanics,
    SocialMechanics,
    InteractionMechanics,
    MenuMechanics,
    CognitionMechanics,
    PlotMechanics,
    NavigationMechanics,
    FluidMechanics,
    Mechanic
)
from app.game.menus.controllers import (
    DisplayController,
    ScrollController,
    MainController,
    LoadController,
    PauseController,
    OptionsController,
    InventoryController
)
from app.models.config import (
    RecipeConfiguration,
    MechanicsInstance
)
from app.models.groups import SpawnableGroup
from app.game.devices import (
    Keyboard,
    Controller
)
from app.services.translators import (
    LambdaTranslator,
    CompilerTranslator
)

class Factory:
    FRAME_MAP = {
        FrameRecipe.SPRITE.value: SpriteFrame,
        FrameRecipe.SINGLE.value: SingleFrame,
        FrameRecipe.ITERABLE.value: IterableFrame,
        FrameRecipe.STATE.value: StateFrame,
        FrameRecipe.TRAVERSAL.value: TraversalFrame,
        FrameRecipe.METER.value: MeterFrame,
        FrameRecipe.INDEX.value: IndexFrame,
        FrameRecipe.FLUID.value: FluidFrame,
        FrameRecipe.SHORELINE.value: ShorelineFrame,
        FrameRecipe.NONE.value: NoFrame
    }

    ANIMATION_MAP = {
        AnimationRecipe.BINARY.value: BinaryAnimation,
        AnimationRecipe.LIFECYCLE.value: LifecycleAnimation,
        AnimationRecipe.STATE.value: StateAnimation,
        AnimationRecipe.SPRITE.value: SpriteAnimation,
        AnimationRecipe.TRAVERSAL.value: TraversalAnimation,
        AnimationRecipe.METER.value: MeterAnimation,
        AnimationRecipe.NONE.value: NoAnimation
    }

    DEVICE_MAP = {
        Devices.KEYBOARD.value: Keyboard,
        Devices.CONTROLLER.value: Controller
    }

    MECHANICS_MAP = {
        Mechanics.ANIMATION.value: AnimationMechanics,
        Mechanics.COLLISION.value: CollisionMechanics,
        Mechanics.PROJECTILE.value: ProjectileMechanics,
        Mechanics.SWITCH.value: SwitchMechanics,
        Mechanics.TRANSITION.value: TransitionMechanics,
        Mechanics.INTERACTION.value: InteractionMechanics,
        Mechanics.PLAYER.value: PlayerMechanics,
        Mechanics.REMOVE.value: RemoveMechanics,
        Mechanics.COMBAT.value: CombatMechanics,
        Mechanics.MOTION.value: MotionMechanics,
        Mechanics.SOCIAL.value: SocialMechanics,
        Mechanics.MENU.value: MenuMechanics,
        Mechanics.COGNITION.value: CognitionMechanics,
        Mechanics.PLOT.value: PlotMechanics,
        Mechanics.NAVIGATION.value: NavigationMechanics,
        Mechanics.FLUID.value: FluidMechanics
    }

    CONTROLLER_MAP  = {
        Controllers.DISPLAY.value: DisplayController,
        Controllers.SCROLL.value: ScrollController,
        Controllers.MAIN.value: MainController,
        Controllers.LOAD.value: LoadController,
        Controllers.PAUSE.value: PauseController,
        Controllers.OPTIONS.value: OptionsController,
        Controllers.INVENTORY.value: InventoryController
    }
    
    TRANSLATOR_MAP = {
        Translators.LAMBDA.value: LambdaTranslator,
        Translators.COMPILER.value: CompilerTranslator
    }

    @staticmethod
    def frame(recipe: Any) -> Frame:
        if isinstance(recipe, str):
            for enum_key, frame_cls in Factory.FRAME_MAP.items():
                if enum_key == recipe:
                    return frame_cls()
        return Factory.FRAME_MAP.get(recipe, NoFrame)()

    @staticmethod
    def animation(recipe: Any) -> Animation:
        if isinstance(recipe, str):
            for enum_key, anim_cls in Factory.ANIMATION_MAP.items():
                if enum_key == recipe:
                    return anim_cls()
        return Factory.ANIMATION_MAP.get(recipe, NoAnimation)()
    
    @staticmethod
    def taxonomy(id: str, name: str, category: str, instance: str) -> Taxonomy:
        return Taxonomy(id, name, category, instance)

    @staticmethod
    def device(dev: str, mapping: dict):
        target_cls = Factory.DEVICE_MAP.get(dev, Keyboard)
        return target_cls(mapping)

    @staticmethod
    def cradle(spawnables: SpawnableGroup, recipes: RecipeConfiguration, decomposer: Any):
        from app.services.generators.game.cradle import Cradle
        return Cradle(spawnables, recipes, decomposer)

    @staticmethod 
    def mechanics(config: MechanicsInstance, executors: Dict[str, Any] = None) -> Mechanic:
        key = config.key

        target_cls = None
        for enum_key, cls in Factory.MECHANICS_MAP.items():
            if enum_key == key:
                target_cls = cls
                break

        if not target_cls:
            target_cls = Factory.MECHANICS_MAP.get(key, AnimationMechanics)

        mechanic_instance = target_cls()

        executor_keys = config.executors
        if executor_keys:
            if executors is None:
                raise KeyError(
                    f"Mechanic '{key}' declared executors {executor_keys}, "
                    f"but no executor registry was provided."
                )
            for executor_key in executor_keys:
                executor = executors.get(executor_key)
                if executor is None:
                    raise KeyError(
                        f"Mechanic '{key}' requested executor '{executor_key}', "
                        f"but it is not registered in the active executor map."
                    )
                mechanic_instance.set_executor(executor_key, executor)

        return mechanic_instance

    @staticmethod
    def controller(kind: Any):
        if isinstance(kind, str):
            for enum_key, cls in Factory.CONTROLLER_MAP.items():
                if enum_key == kind:
                    return cls()
        return Factory.CONTROLLER_MAP.get(kind, ScrollController)()

    @staticmethod
    def translator(translation: str):
        target_cls = Factory.TRANSLATOR_MAP.get(translation, LambdaTranslator)
        return target_cls()

    @staticmethod
    def context(menu: str, **kwargs):
        # TODO
        pass