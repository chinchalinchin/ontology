"""
@domain.system
@app.service
@app.asset
@workflow.injection
@workflow.compositions

# Ontology: Source - app.services.factories.assets

Factory for instantiating Assets and flyweight Asset components.
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
    NoAnimation
)
from app.assets.frames import (
    BinaryFrame,
    CardinalFrame,
    FluidFrame,
    IconFrame,
    IterableFrame,
    MaterialFrame,
    MeterFrame,
    NoFrame,
    ObjectFrame,
    PaneFrame,
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
    FrameRecipe,
    HitboxRecipe,
    Substrates
)


class AssetFactory:
    """
    Central factory for Asset assembly and flyweight component resolution.
    """
    # ----------- FLYWEIGHT COMPONENTS
    _FRAMES = {
        FrameRecipe.BINARY: BinaryFrame(),
        FrameRecipe.CARDINAL: CardinalFrame(),
        FrameRecipe.FLUID: FluidFrame(),
        FrameRecipe.ICON: IconFrame(),
        FrameRecipe.ITERABLE: IterableFrame(),
        FrameRecipe.MATERIAL: MaterialFrame(),
        FrameRecipe.METER: MeterFrame(),
        FrameRecipe.NONE: NoFrame(),
        FrameRecipe.OBJECT: ObjectFrame(),
        FrameRecipe.PANE: PaneFrame(),
        FrameRecipe.SEASONAL: SeasonalFrame(),
        FrameRecipe.SINGLE: SingleFrame(),
        FrameRecipe.SPRITE: SpriteFrame(),
        FrameRecipe.STAGE: StageFrame(),
        FrameRecipe.STATE: StateFrame(),
        FrameRecipe.TRAVERSAL: TraversalFrame(),
    }

    _ANIMATIONS = {
        AnimationRecipe.FREQUENCY: FrequencyAnimation(),
        AnimationRecipe.NONE: NoAnimation(),
        AnimationRecipe.SPRITE: SpriteAnimation(),
        AnimationRecipe.STATE: StateAnimation(),
    }

    _HITBOXES = {
        HitboxRecipe.ATTACK: AttackHitbox(),
        HitboxRecipe.DYNAMIC: DynamicHitbox(),
        HitboxRecipe.ELEVATED: ElevatedHitbox(),
        HitboxRecipe.LAYERED: LayeredHitbox(),
        HitboxRecipe.MATERIAL: MaterialHitbox(),
        HitboxRecipe.NONE: NoHitbox(),
        HitboxRecipe.STAGE: StageHitbox(),
        HitboxRecipe.STATIC: StaticHitbox(),
        HitboxRecipe.SWITCH: SwitchHitbox(),
    }

    @classmethod
    def frame(cls, recipe: str) -> Frame:
        return cls._FRAMES.get(recipe, cls._FRAMES[FrameRecipe.NONE])

    @classmethod
    def animation(cls, recipe: str) -> Animation:
        return cls._ANIMATIONS.get(recipe, cls._ANIMATIONS[AnimationRecipe.NONE])

    @classmethod
    def hitbox(cls, recipe: str) -> HitboxSchema:
        return cls._HITBOXES.get(recipe, cls._HITBOXES[HitboxRecipe.STATIC])

    @classmethod
    def asset(cls,
        category: str,
        instance: str,
        properties: AssetProperties,
        state: AssetState,
        recipe: Recipe,
        substrate: int = Substrates.STANDARD
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
    def widget(cls,
        node: MenuNode,
        properties: WidgetProperties,
        state: WidgetState,
        recipe: Recipe,
        binding: Optional[Binding] = None           
    ) -> Widget:
        animation = cls.animation(recipe.animation)
        frame = cls.frame(recipe.frame)
        taxonomy = Taxonomy(
            node.id, 
            node.name, 
            AssetCategories.WIDGETS, 
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