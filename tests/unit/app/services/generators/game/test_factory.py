"""
# Ontology: tests.unit.test_app_services_generators_game_factory
"""
# Standard Libraries
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    AssetCategories,
    FrameRecipe,
    AnimationRecipe,
    Devices,
    Mechanics,
    Controllers,
    Translators
)
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
    FrequencyAnimation,
    StateAnimation,
    SpriteAnimation,
    TraversalAnimation,
    MeterAnimation,
    NoAnimation
)
from app.game.devices import (
    Keyboard, 
    Controller
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
    FluidMechanics
)
from app.models.config import (
    MappingConfiguration,
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
from app.services.translators import (
    LambdaTranslator, 
    CompilerTranslator
)
from app.services.factories import (
    AssetFactory,
    MechanicFactory,
)
from app.services.generators.game import (
    Cradle
)


@pytest.mark.app_services
def test_factory_frame():
    assert isinstance(
        AssetFactory.frame(FrameRecipe.SPRITE.value), 
        SpriteFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.SINGLE.value), 
        SingleFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.ITERABLE.value), 
        IterableFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.STATE.value), 
        StateFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.TRAVERSAL.value), 
        TraversalFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.METER.value), 
        MeterFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.INDEX.value), 
        IndexFrame
    )
    assert isinstance(
        AssetFactory.frame(FrameRecipe.NONE.value), 
        NoFrame
    )
    assert isinstance(
        AssetFactory.frame("unknown_frame"),
        NoFrame
    )
    assert isinstance(
        AssetFactory.frame(None), 
        NoFrame
    )


@pytest.mark.app_services
def test_factory_animation():
    assert isinstance(
        AssetFactory.animation(AnimationRecipe.FREQUENCY.value), 
        FrequencyAnimation
    )
    assert isinstance(
        AssetFactory.animation(AnimationRecipe.STATE.value), 
        StateAnimation
    )
    assert isinstance(
        AssetFactory.animation(AnimationRecipe.SPRITE.value),
        SpriteAnimation
    )
    assert isinstance(
        AssetFactory.animation(AnimationRecipe.TRAVERSAL.value), 
        TraversalAnimation
    )
    assert isinstance(
        AssetFactory.animation(AnimationRecipe.METER.value), 
        MeterAnimation
    )
    assert isinstance(
        AssetFactory.animation(AnimationRecipe.NONE.value), 
        NoAnimation
    )
    assert isinstance(
        AssetFactory.animation("unknown_anim"),
        NoAnimation
    )
    assert isinstance(
        AssetFactory.animation(None),
        NoAnimation
    )


def test_factory_device(mock_mapping_configuration: MappingConfiguration):
    kb = AssetFactory.device(
        Devices.KEYBOARD.value, 
        mock_mapping_configuration.keyboard
    )
    assert isinstance(kb, Keyboard)

    ctrl = AssetFactory.device(
        Devices.CONTROLLER.value, 
        mock_mapping_configuration.controller
    )
    assert isinstance(ctrl, Controller)

    fallback = AssetFactory.device(
        "unknown_device", 
        mock_mapping_configuration.keyboard
    )
    assert isinstance(fallback, Keyboard)


def test_factory_cradle(
    mock_spawnables, 
    mock_recipes_configuration,
    mock_decomposer
):
    cradle = AssetFactory.cradle(
        mock_spawnables, 
        mock_recipes_configuration, 
        mock_decomposer
    )
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
        assert isinstance(MechanicFactory.mechanics(instance), cls)

    unmapped_instance = MechanicsInstance(
        key="unmapped_mechanics",
        executors= []
    )
    assert isinstance(
        MechanicFactory.mechanics(unmapped_instance), 
        AnimationMechanics
    )


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
        assert isinstance(AssetFactory.controller(enum_key), cls)

    assert isinstance(
        AssetFactory.controller("unmapped_controller"), 
        ScrollController
    )


def test_factory_translator():
    assert isinstance(
        MechanicFactory.translator(Translators.LAMBDA.value), 
        LambdaTranslator
    )
    assert isinstance(
        MechanicFactory.translator(Translators.COMPILER.value), 
        CompilerTranslator
    )
    assert isinstance(
        MechanicFactory.translator("unmapped_translator"), 
        LambdaTranslator
    )