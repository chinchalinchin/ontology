"""
@domain.test
@test.unit
@app.services
@workflow.injection

# Ontology: Tests - tests.unit.app.services.generators.game.test_factories

Unit tests for Application Factories.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AnimationRecipe,
    Controllers,
    Devices,
    FrameRecipe,
    HitboxRecipe,
    Mechanics,
    Translators,
)
from app.assets.frames import (
    BinaryFrame,
    CardinalFrame,
    FluidFrame,
    IndexFrame,
    IterableFrame,
    MaterialFrame,
    MeterFrame,
    NoFrame,
    ObjectFrame,
    SeasonalFrame,
    SingleFrame,
    SpriteFrame,
    StageFrame,
    StateFrame,
    TraversalFrame,
)
from app.assets.animations import (
    FrequencyAnimation,
    MeterAnimation,
    NoAnimation,
    SpriteAnimation,
    StateAnimation,
    TraversalAnimation,
)
from app.assets.hitboxes import (
    AttackHitbox,
    DynamicHitbox,
    ElevatedHitbox,
    LayeredHitbox,
    MaterialHitbox,
    NoHitbox,
    StageHitbox,
    StaticHitbox,
    SwitchHitbox,
)
from app.game.devices import (
    Controller,
    Keyboard,
)
from app.game.logic.mechanics import (
    AnimationMechanics,
    CognitionMechanics,
    CollisionMechanics,
    CombatMechanics,
    FluidMechanics,
    InteractionMechanics,
    MenuMechanics,
    MotionMechanics,
    NavigationMechanics,
    PlayerMechanics,
    PlotMechanics,
    ProjectileMechanics,
    RemoveMechanics,
    SeasonMechanics,
    SocialMechanics,
    SwitchMechanics,
    TelemetryMechanics,
    TransitionMechanics,
)
from app.models.config import (
    ConfigurationSchema,
    MechanicsInstance,
)
from app.game.menus.controllers import (
    DisplayController,
    InventoryController,
    LoadController,
    MainController,
    OptionsController,
    PauseController,
    ScrollController,
)
from app.services.translators import (
    CompilerTranslator,
    LambdaTranslator,
)
from app.services.factories import (
    AssetFactory,
    MechanicFactory,
)

# ------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_services,
    pytest.mark.workflow_injection,
]

# ------------------------------------------------------------------


@pytest.mark.app_asset
@pytest.mark.asset_frame
def test_factory_frame():
    mapping = {
        FrameRecipe.BINARY.value: BinaryFrame,
        FrameRecipe.CARDINAL.value: CardinalFrame,
        FrameRecipe.FLUID.value: FluidFrame,
        FrameRecipe.INDEX.value: IndexFrame,
        FrameRecipe.ITERABLE.value: IterableFrame,
        FrameRecipe.MATERIAL.value: MaterialFrame,
        FrameRecipe.METER.value: MeterFrame,
        FrameRecipe.NONE.value: NoFrame,
        FrameRecipe.OBJECT.value: ObjectFrame,
        FrameRecipe.SEASONAL.value: SeasonalFrame,
        FrameRecipe.SINGLE.value: SingleFrame,
        FrameRecipe.SPRITE.value: SpriteFrame,
        FrameRecipe.STAGE.value: StageFrame,
        FrameRecipe.STATE.value: StateFrame,
        FrameRecipe.TRAVERSAL.value: TraversalFrame,
    }
    for recipe_key, cls in mapping.items():
        assert isinstance(AssetFactory.frame(recipe_key), cls)

    assert isinstance(AssetFactory.frame("unknown_frame"), NoFrame)
    assert isinstance(AssetFactory.frame(None), NoFrame)


@pytest.mark.app_asset
@pytest.mark.asset_animation
def test_factory_animation():
    mapping = {
        AnimationRecipe.FREQUENCY.value: FrequencyAnimation,
        AnimationRecipe.METER.value: MeterAnimation,
        AnimationRecipe.NONE.value: NoAnimation,
        AnimationRecipe.SPRITE.value: SpriteAnimation,
        AnimationRecipe.STATE.value: StateAnimation,
        AnimationRecipe.TRAVERSAL.value: TraversalAnimation,
    }
    for recipe_key, cls in mapping.items():
        assert isinstance(AssetFactory.animation(recipe_key), cls)

    assert isinstance(AssetFactory.animation("unknown_anim"), NoAnimation)
    assert isinstance(AssetFactory.animation(None), NoAnimation)


@pytest.mark.app_asset
@pytest.mark.asset_hitbox
def test_factory_hitbox():
    mapping = {
        HitboxRecipe.ATTACK.value: AttackHitbox,
        HitboxRecipe.DYNAMIC.value: DynamicHitbox,
        HitboxRecipe.ELEVATED.value: ElevatedHitbox,
        HitboxRecipe.LAYERED.value: LayeredHitbox,
        HitboxRecipe.MATERIAL.value: MaterialHitbox,
        HitboxRecipe.NONE.value: NoHitbox,
        HitboxRecipe.STAGE.value: StageHitbox,
        HitboxRecipe.STATIC.value: StaticHitbox,
        HitboxRecipe.SWITCH.value: SwitchHitbox,
    }
    for recipe_key, cls in mapping.items():
        assert isinstance(AssetFactory.hitbox(recipe_key), cls)

    assert isinstance(AssetFactory.hitbox("unknown_hitbox"), StaticHitbox)
    assert isinstance(AssetFactory.hitbox(None), StaticHitbox)


@pytest.mark.app_component
def test_factory_device(mock_configurations_schema: ConfigurationSchema):
    mappings = mock_configurations_schema.mappings

    kb = MechanicFactory.device(
        Devices.KEYBOARD.value,
        mappings.keyboard,
    )
    assert isinstance(kb, Keyboard)

    ctrl = MechanicFactory.device(
        Devices.CONTROLLER.value,
        mappings.controller,
    )
    assert isinstance(ctrl, Controller)

    fallback = MechanicFactory.device(
        "unknown_device",
        mappings.keyboard,
    )
    assert isinstance(fallback, Keyboard)


@pytest.mark.app_core
def test_factory_mechanics():
    mapping = {
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
    for enum_key, cls in mapping.items():
        instance = MechanicsInstance(
            key=enum_key,
            executors=[],
        )
        assert isinstance(MechanicFactory.mechanics(instance), cls)

    unmapped_instance = MechanicsInstance(
        key="unmapped_mechanics",
        executors=[],
    )
    assert isinstance(
        MechanicFactory.mechanics(unmapped_instance),
        AnimationMechanics,
    )


@pytest.mark.workflow_menus
def test_factory_controller():
    mapping = {
        Controllers.DISPLAY.value: DisplayController,
        Controllers.SCROLL.value: ScrollController,
        Controllers.MAIN.value: MainController,
        Controllers.LOAD.value: LoadController,
        Controllers.PAUSE.value: PauseController,
        Controllers.OPTIONS.value: OptionsController,
        Controllers.INVENTORY.value: InventoryController,
    }
    for enum_key, cls in mapping.items():
        assert isinstance(AssetFactory.controller(enum_key), cls)

    assert isinstance(
        AssetFactory.controller("unmapped_controller"),
        ScrollController,
    )


@pytest.mark.workflow_ecology
@pytest.mark.workflow_intentions
@pytest.mark.workflow_plots
@pytest.mark.workflow_seasons
def test_factory_translator():
    assert isinstance(
        MechanicFactory.translator(Translators.LAMBDA.value),
        LambdaTranslator,
    )
    assert isinstance(
        MechanicFactory.translator(Translators.COMPILER.value),
        CompilerTranslator,
    )
    assert isinstance(
        MechanicFactory.translator("unmapped_translator"),
        LambdaTranslator,
    )