"""
# Ontology: tests.unit.test_app_services_generators_game_factory
"""
from unittest.mock import MagicMock

from app.config.enums import (
    FrameRecipe,
    AnimationRecipe,
    Devices,
    Mechanics,
    Controllers,
    Translators
)
from app.services.generators.game.factory import Factory
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
from app.assets.animations import (
    BinaryAnimation,
    LifecycleAnimation,
    StateAnimation,
    SpriteAnimation,
    TraversalAnimation,
    MeterAnimation,
    NoAnimation
)
from app.game.devices import Keyboard, Controller
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
    FluidMechanics
)
from app.models.config import (
    DeviceMapping,
    MechanicsInstance
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
from app.services.translators import LambdaTranslator, CompilerTranslator
from app.services.generators.game.cradle import Cradle


def test_factory_frame():
    assert isinstance(Factory.frame(FrameRecipe.SPRITE.value), SpriteFrame)
    assert isinstance(Factory.frame(FrameRecipe.SINGLE.value), SingleFrame)
    assert isinstance(Factory.frame(FrameRecipe.ITERABLE.value), IterableFrame)
    assert isinstance(Factory.frame(FrameRecipe.STATE.value), StateFrame)
    assert isinstance(Factory.frame(FrameRecipe.TRAVERSAL.value), TraversalFrame)
    assert isinstance(Factory.frame(FrameRecipe.METER.value), MeterFrame)
    assert isinstance(Factory.frame(FrameRecipe.INDEX.value), IndexFrame)
    assert isinstance(Factory.frame(FrameRecipe.NONE.value), NoFrame)

    assert isinstance(Factory.frame("sprite"), SpriteFrame)
    assert isinstance(Factory.frame("single"), SingleFrame)
    assert isinstance(Factory.frame("unknown_frame"), NoFrame)
    assert isinstance(Factory.frame(None), NoFrame)


def test_factory_animation():
    assert isinstance(Factory.animation(AnimationRecipe.BINARY.value), BinaryAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.LIFECYCLE.value), LifecycleAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.STATE.value), StateAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.SPRITE.value), SpriteAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.TRAVERSAL.value), TraversalAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.METER.value), MeterAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.NONE.value), NoAnimation)

    assert isinstance(Factory.animation("binary"), BinaryAnimation)
    assert isinstance(Factory.animation("lifecycle"), LifecycleAnimation)
    assert isinstance(Factory.animation("unknown_anim"), NoAnimation)
    assert isinstance(Factory.animation(None), NoAnimation)


def test_factory_taxonomy():
    tax = Factory.taxonomy("sheet-1", "hero", "sheets", "players")
    assert tax.id == "sheet-1"
    assert tax.name == "hero"
    assert tax.category == "sheets"
    assert tax.instance == "players"


def test_factory_device(mock_mapping: DeviceMapping):
    kb = Factory.device(Devices.KEYBOARD.value, mock_mapping)
    assert isinstance(kb, Keyboard)

    ctrl = Factory.device(Devices.CONTROLLER.value, mock_mapping)
    assert isinstance(ctrl, Controller)

    fallback = Factory.device("unknown_device", mock_mapping)
    assert isinstance(fallback, Keyboard)

def test_factory_cradle(mock_spawnables, mock_recipes):
    decomposer = MagicMock()
    cradle = Factory.cradle(mock_spawnables, mock_recipes, decomposer)
    assert isinstance(cradle, Cradle)


def test_factory_mechanics():
    mapping = {
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
    for enum_key, cls in mapping.items():
        instance = MechanicsInstance(
            key=enum_key,
            executors=[]
        )
        assert isinstance(Factory.mechanics(instance), cls)

    unmapped_instance = MechanicsInstance(
        key="unmapped_mechanics",
        executors= []
    )
    assert isinstance(Factory.mechanics(unmapped_instance), AnimationMechanics)


def test_factory_controller():
    mapping = {
        Controllers.DISPLAY.value: DisplayController,
        Controllers.SCROLL.value: ScrollController,
        Controllers.MAIN.value: MainController,
        Controllers.LOAD.value: LoadController,
        Controllers.PAUSE.value: PauseController,
        Controllers.OPTIONS.value: OptionsController,
        Controllers.INVENTORY.value: InventoryController
    }
    for enum_key, cls in mapping.items():
        assert isinstance(Factory.controller(enum_key), cls)

    assert isinstance(Factory.controller("unmapped_controller"), ScrollController)


def test_factory_translator():
    assert isinstance(Factory.translator(Translators.LAMBDA.value), LambdaTranslator)
    assert isinstance(Factory.translator(Translators.COMPILER.value), CompilerTranslator)
    assert isinstance(Factory.translator("unmapped_translator"), LambdaTranslator)