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
    RecipeConfiguration
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
        FrameRecipe.SPRITE: SpriteFrame,
        FrameRecipe.SINGLE: SingleFrame,
        FrameRecipe.ITERABLE: IterableFrame,
        FrameRecipe.STATE: StateFrame,
        FrameRecipe.TRAVERSAL: TraversalFrame,
        FrameRecipe.METER: MeterFrame,
        FrameRecipe.INDEX: IndexFrame,
        FrameRecipe.FLUID: FluidFrame,
        FrameRecipe.SHORELINE: ShorelineFrame,
        FrameRecipe.NONE: NoFrame
    }

    ANIMATION_MAP = {
        AnimationRecipe.BINARY: BinaryAnimation,
        AnimationRecipe.LIFECYCLE: LifecycleAnimation,
        AnimationRecipe.STATE: StateAnimation,
        AnimationRecipe.SPRITE: SpriteAnimation,
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
        Mechanics.TRANSITION: TransitionMechanics,
        Mechanics.INTERACTION: InteractionMechanics,
        Mechanics.PLAYER: PlayerMechanics,
        Mechanics.REMOVE: RemoveMechanics,
        Mechanics.COMBAT: CombatMechanics,
        Mechanics.MOTION: MotionMechanics,
        Mechanics.SOCIAL: SocialMechanics,
        Mechanics.MENU: MenuMechanics,
        Mechanics.COGNITION: CognitionMechanics,
        Mechanics.PLOT: PlotMechanics,
        Mechanics.NAVIGATION: NavigationMechanics,
        Mechanics.FLUID: FluidMechanics
    }

    CONTROLLER_MAP  = {
        Controllers.DISPLAY: DisplayController,
        Controllers.SCROLL: ScrollController,
        Controllers.MAIN: MainController,
        Controllers.LOAD: LoadController,
        Controllers.PAUSE: PauseController,
        Controllers.OPTIONS: OptionsController,
        Controllers.INVENTORY: InventoryController
    }
    
    TRANSLATOR_MAP = {
        Translators.LAMBDA: LambdaTranslator,
        Translators.COMPILER: CompilerTranslator
    }

    @staticmethod
    def frame(recipe: Any) -> Frame:
        if isinstance(recipe, str):
            for enum_key, frame_cls in Factory.FRAME_MAP.items():
                if enum_key.value == recipe:
                    return frame_cls()
        return Factory.FRAME_MAP.get(recipe, NoFrame)()

    @staticmethod
    def animation(recipe: Any) -> Animation:
        if isinstance(recipe, str):
            for enum_key, anim_cls in Factory.ANIMATION_MAP.items():
                if enum_key.value == recipe:
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
    def mechanics(config: Any, executors: Dict[str, Any] = None) -> Mechanic:
        key = getattr(config, "key", None)
        if key is None:
            key = config.value if hasattr(config, "value") else str(config)

        target_cls = None
        for enum_key, cls in Factory.MECHANICS_MAP.items():
            if enum_key.value == key or enum_key == key:
                target_cls = cls
                break

        if not target_cls:
            target_cls = Factory.MECHANICS_MAP.get(key)

        if not target_cls:
            raise KeyError(f"No mechanic class registered for key: '{key}'")

        mechanic_instance = target_cls()

        executor_keys = getattr(config, "executors", [])
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
                if enum_key.value == kind:
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