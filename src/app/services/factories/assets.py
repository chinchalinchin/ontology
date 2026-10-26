"""
@domain.system
@app.services
@workflow.injection
@workflow.compositions

# Ontology: Source - app.services.factories.assets

Factory for instantiating Assets, flyweight Asset components, and Menu Controllers.
"""
# Standard Libraries
from typing import Optional

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
from app.game.menus.bindings import Binding
from app.game.menus.core import Widget
from app.game.menus.controllers import (
    DisplayController,
    InventoryController,
    LoadController,
    MainController,
    OptionsController,
    PauseController,
    ScrollController
)
from app.models.config import (
    Recipe,
    MenuNode
)
from app.models.properties import (
    AssetProperties,
    WidgetProperties
)
from app.models.state import (
    AssetState,
    WidgetState
)
from app.static.semantics import (
    AssetCategories,
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

    @classmethod
    def asset(cls,
        category: str,
        instance: str,
        properties: AssetProperties,
        state: AssetState,
        recipe: Recipe,
        substrate: int = Substrates.STANDARD.value
    ) -> Asset:
        """
        Unified point of instantiation for all in-game Assets.
        """
        animation = cls.animation(recipe.animation)
        frame = cls.frame(recipe.frame)
        hitbox = cls.hitbox(recipe.hitbox)
        taxonomy = Taxonomy(state.id, state.name, category, instance)
        return Asset(
            taxonomy=taxonomy,
            properties=properties,
            state=state,
            frame=frame,
            animation=animation,
            hitbox=hitbox,
            substrate=substrate
        )

    @classmethod
    def controller(cls, kind: str):
        target_cls = cls.CONTROLLER_MAP.get(kind, ScrollController)
        return target_cls()

    @classmethod
    def widget(cls,
        node: MenuNode,
        properties: WidgetProperties,
        state: WidgetState,
        recipe: Recipe,
        binding: Optional[Binding] = None           
    ):
        animation = cls.animation(recipe.animation)
        frame = cls.frame(recipe.frame)
        taxonomy = Taxonomy(
            node.id, 
            node.name, 
            AssetCategories.WIDGETS.value, 
            node.instance
        )
        return Widget(
            taxonomy=taxonomy,
            properties=properties,
            state=state,
            frame=frame,
            animation=animation,
            binding=binding
        )