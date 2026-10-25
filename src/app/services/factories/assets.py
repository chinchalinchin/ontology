"""
@domain.system
@app.services
@workflow.injections
@workflow.compositions

# Ontology: Source - app.services.factories.assets

Factory for instantiating Assets, flyweight Asset components, and Menu Controllers.
"""
# Standard Libraries
from typing import Any

# Application Libraries
from app.assets.base import (
    Asset,
    Taxonomy,
    Frame,
    Animation,
    HitboxSchema
)
from app.assets.animations import (
    FrequencyAnimation,
    StateAnimation,
    SpriteAnimation,
    TraversalAnimation,
    MeterAnimation,
    NoAnimation
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
    TraversalFrame
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
    SwitchHitbox
)
from app.game.menus.controllers import (
    DisplayController,
    InventoryController,
    LoadController,
    MainController,
    OptionsController,
    PauseController,
    ScrollController
)
from app.models.properties import AssetProperties
from app.models.state import AssetState
from app.static.semantics import (
    AnimationRecipe,
    Controllers,
    FrameRecipe,
    HitboxRecipe,
    Substrates
)


class AssetFactory:
    """
    Central factory for Asset assembly, flyweight component resolution,
    and temporary Menu Controller instantiation.
    """
    # ----------- FLYWEIGHT COMPONENTS
    _FRAMES = {
        FrameRecipe.BINARY.value: BinaryFrame(),
        FrameRecipe.CARDINAL.value: CardinalFrame(),
        FrameRecipe.FLUID.value: FluidFrame(),
        FrameRecipe.INDEX.value: IndexFrame(),
        FrameRecipe.ITERABLE.value: IterableFrame(),
        FrameRecipe.MATERIAL.value: MaterialFrame(),
        FrameRecipe.METER.value: MeterFrame(),
        FrameRecipe.NONE.value: NoFrame(),
        FrameRecipe.OBJECT.value: ObjectFrame(),
        FrameRecipe.SEASONAL.value: SeasonalFrame(),
        FrameRecipe.SINGLE.value: SingleFrame(),
        FrameRecipe.SPRITE.value: SpriteFrame(),
        FrameRecipe.STAGE.value: StageFrame(),
        FrameRecipe.STATE.value: StateFrame(),
        FrameRecipe.TRAVERSAL.value: TraversalFrame(),
    }

    _ANIMATIONS = {
        AnimationRecipe.FREQUENCY.value: FrequencyAnimation(),
        AnimationRecipe.METER.value: MeterAnimation(),
        AnimationRecipe.NONE.value: NoAnimation(),
        AnimationRecipe.SPRITE.value: SpriteAnimation(),
        AnimationRecipe.STATE.value: StateAnimation(),
        AnimationRecipe.TRAVERSAL.value: TraversalAnimation(),
    }

    _HITBOXES = {
        HitboxRecipe.ATTACK.value: AttackHitbox(),
        HitboxRecipe.DYNAMIC.value: DynamicHitbox(),
        HitboxRecipe.ELEVATED.value: ElevatedHitbox(),
        HitboxRecipe.LAYERED.value: LayeredHitbox(),
        HitboxRecipe.MATERIAL.value: MaterialHitbox(),
        HitboxRecipe.NONE.value: NoHitbox(),
        HitboxRecipe.STAGE.value: StageHitbox(),
        HitboxRecipe.STATIC.value: StaticHitbox(),
        HitboxRecipe.SWITCH.value: SwitchHitbox(),
    }

    # ------------ MENU CONTROLLERS (Pending app.services.factories.menus)
    CONTROLLER_MAP = {
        Controllers.DISPLAY.value: DisplayController,
        Controllers.INVENTORY.value: InventoryController,
        Controllers.LOAD.value: LoadController,
        Controllers.MAIN.value: MainController,
        Controllers.OPTIONS.value: OptionsController,
        Controllers.PAUSE.value: PauseController,
        Controllers.SCROLL.value: ScrollController,
    }

    @classmethod
    def frame(cls, recipe: str) -> Frame:
        return cls._FRAMES.get(recipe, cls._FRAMES[FrameRecipe.NONE.value])

    @classmethod
    def animation(cls, recipe: str) -> Animation:
        return cls._ANIMATIONS.get(recipe, cls._ANIMATIONS[AnimationRecipe.NONE.value])

    @classmethod
    def hitbox(cls, recipe: str) -> HitboxSchema:
        return cls._HITBOXES.get(recipe, cls._HITBOXES[HitboxRecipe.STATIC.value])

    @staticmethod
    def taxonomy(id: str, name: str, category: str, instance: str) -> Taxonomy:
        return Taxonomy(id=id, name=name, category=category, instance=instance)

    @classmethod
    def asset(
        cls,
        category: str,
        instance: str,
        properties: AssetProperties,
        state: AssetState,
        recipe: Any,
        substrate: int = Substrates.STANDARD.value
    ) -> Asset:
        """
        Unified point of instantiation for all in-game Assets.
        """
        return Asset(
            taxonomy=cls.taxonomy(
                id=state.id,
                name=state.name,
                category=category,
                instance=instance
            ),
            properties=properties,
            state=state,
            frame=cls.frame(recipe.frame),
            animation=cls.animation(recipe.animation),
            hitbox=cls.hitbox(recipe.hitbox),
            substrate=substrate
        )

    @classmethod
    def controller(cls, kind: str):
        target_cls = cls.CONTROLLER_MAP.get(kind, ScrollController)
        return target_cls()