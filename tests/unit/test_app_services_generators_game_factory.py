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
from app.models.config import DeviceMapping
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
    assert isinstance(Factory.frame(FrameRecipe.SPRITE), SpriteFrame)
    assert isinstance(Factory.frame(FrameRecipe.SINGLE), SingleFrame)
    assert isinstance(Factory.frame(FrameRecipe.ITERABLE), IterableFrame)
    assert isinstance(Factory.frame(FrameRecipe.STATE), StateFrame)
    assert isinstance(Factory.frame(FrameRecipe.TRAVERSAL), TraversalFrame)
    assert isinstance(Factory.frame(FrameRecipe.METER), MeterFrame)
    assert isinstance(Factory.frame(FrameRecipe.INDEX), IndexFrame)
    assert isinstance(Factory.frame(FrameRecipe.NONE), NoFrame)

    assert isinstance(Factory.frame("sprite"), SpriteFrame)
    assert isinstance(Factory.frame("single"), SingleFrame)
    assert isinstance(Factory.frame("unknown_frame"), NoFrame)
    assert isinstance(Factory.frame(None), NoFrame)


def test_factory_animation():
    assert isinstance(Factory.animation(AnimationRecipe.BINARY), BinaryAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.LIFECYCLE), LifecycleAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.STATE), StateAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.SPRITE), SpriteAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.TRAVERSAL), TraversalAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.METER), MeterAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.NONE), NoAnimation)

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
    kb = Factory.device(Devices.KEYBOARD, mock_mapping)
    assert isinstance(kb, Keyboard)

    ctrl = Factory.device(Devices.CONTROLLER, mock_mapping)
    assert isinstance(ctrl, Controller)

    fallback = Factory.device("unknown_device", mock_mapping)
    assert isinstance(fallback, Keyboard)

def test_factory_cradle(mock_spawnables, mock_recipes):
    decomposer = MagicMock()
    cradle = Factory.cradle(mock_spawnables, mock_recipes, decomposer)
    assert isinstance(cradle, Cradle)


def test_factory_mechanics():
    mapping = {
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
    for enum_key, cls in mapping.items():
        assert isinstance(Factory.mechanics(enum_key), cls)
        assert isinstance(Factory.mechanics(enum_key.value), cls)

    assert isinstance(Factory.mechanics("unmapped_mechanic"), AnimationMechanics)


def test_factory_controller():
    mapping = {
        Controllers.DISPLAY: DisplayController,
        Controllers.SCROLL: ScrollController,
        Controllers.MAIN: MainController,
        Controllers.LOAD: LoadController,
        Controllers.PAUSE: PauseController,
        Controllers.OPTIONS: OptionsController,
        Controllers.INVENTORY: InventoryController
    }
    for enum_key, cls in mapping.items():
        assert isinstance(Factory.controller(enum_key), cls)
        assert isinstance(Factory.controller(enum_key.value), cls)

    assert isinstance(Factory.controller("unmapped_controller"), ScrollController)


def test_factory_translator():
    assert isinstance(Factory.translator(Translators.LAMBDA), LambdaTranslator)
    assert isinstance(Factory.translator(Translators.COMPILER), CompilerTranslator)
    assert isinstance(Factory.translator("unmapped_translator"), LambdaTranslator)