"""
# Ontology: app.services.orchestration.factory

Package for instantiating Asset classes and their components.
"""
# Standard Libraries
from typing import Any, Dict, Optional

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
    Animation,
    HitboxSchema
)
from app.assets.hitboxes import (
    StaticHitbox,
    StageHitbox,
    DynamicHitbox,
    AttackHitbox,
    NoHitbox
)
from app.assets.frames import (
    SingleFrame, 
    IterableFrame, 
    StateFrame,
    SpriteFrame,
    FluidFrame,
    CardinalFrame,
    TraversalFrame,
    MeterFrame,
    IndexFrame,
    OrientedFrame,
    StageFrame,
    SeasonalFrame,
    NoFrame
)
from app.config.enums import (
    AnimationRecipe, 
    FrameRecipe, 
    HitboxRecipe,
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
    SeasonMechanics,
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
        FrameRecipe.CARDINAL.value: CardinalFrame,
        FrameRecipe.INDEX.value: IndexFrame,
        FrameRecipe.ITERABLE.value: IterableFrame,
        FrameRecipe.FLUID.value: FluidFrame,
        FrameRecipe.METER.value: MeterFrame,
        FrameRecipe.NONE.value: NoFrame,
        FrameRecipe.ORIENTED.value: OrientedFrame,
        FrameRecipe.SEASONAL.value: SeasonalFrame,
        FrameRecipe.SPRITE.value: SpriteFrame,
        FrameRecipe.SINGLE.value: SingleFrame,
        FrameRecipe.STAGE.value: StageFrame,
        FrameRecipe.STATE.value: StateFrame,
        FrameRecipe.TRAVERSAL.value: TraversalFrame,
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

    HITBOX_MAP = {
        HitboxRecipe.STATIC.value: StaticHitbox,
        HitboxRecipe.DYNAMIC.value: DynamicHitbox,
        HitboxRecipe.STAGE.value: StageHitbox,
        HitboxRecipe.ATTACK.value: AttackHitbox,
        HitboxRecipe.NONE.value: NoHitbox
    }

    DEVICE_MAP = {
        Devices.KEYBOARD.value: Keyboard,
        Devices.CONTROLLER.value: Controller
    }

    MECHANICS_MAP = {
        Mechanics.ANIMATION.value: AnimationMechanics,
        Mechanics.COGNITION.value: CognitionMechanics,
        Mechanics.COLLISION.value: CollisionMechanics,
        Mechanics.COMBAT.value: CombatMechanics,
        Mechanics.FLUID.value: FluidMechanics,
        Mechanics.INTERACTION.value: InteractionMechanics,
        Mechanics.MENU.value: MenuMechanics,
        Mechanics.MOTION.value: MotionMechanics,
        Mechanics.NAVIGATION.value: NavigationMechanics,
        Mechanics.PLAYER.value: PlayerMechanics,
        Mechanics.PLOT.value: PlotMechanics,
        Mechanics.PROJECTILE.value: ProjectileMechanics,
        Mechanics.REMOVE.value: RemoveMechanics,
        Mechanics.SEASON.value: SeasonMechanics,
        Mechanics.SOCIAL.value: SocialMechanics,
        Mechanics.SWITCH.value: SwitchMechanics,
        Mechanics.TRANSITION.value: TransitionMechanics,
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
    def mechanics(
        config: MechanicsInstance, 
        executors: Dict[str, Any] = None,
        relations: Dict[str, Any] = None
    ) -> Mechanic:
        key = config.key

        target_cls = None
        for enum_key, cls in Factory.MECHANICS_MAP.items():
            if enum_key == key:
                target_cls = cls
                break

        if not target_cls:
            target_cls = Factory.MECHANICS_MAP.get(key, AnimationMechanics)

        mechanic_instance = target_cls()

        # 1. Resolve and inject executors
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

        # 2. Resolve and inject relations
        relation_keys = config.relations
        if relation_keys:
            if relations is None:
                raise KeyError(
                    f"Mechanic '{key}' declared relations {relation_keys}, "
                    f"but no relations registry was provided."
                )
            for relation_key in relation_keys:
                relation = relations.get(relation_key)
                if relation is None:
                    raise KeyError(
                        f"Mechanic '{key}' requested relation '{relation_key}', "
                        f"but it is not registered in the active relations map."
                    )
                mechanic_instance.set_relation(relation_key, relation)

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
    def hitbox(schema: str):
        target_cls = Factory.HITBOX_MAP.get(schema, StaticHitbox)
        return target_cls()
    
    @staticmethod
    def context(menu: str, **kwargs):
        # TODO
        pass