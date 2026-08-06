"""
# Ontology: Factory
"""
# Application Librarires
from app.assets.animations import BinaryAnimation, \
                                    PersistentAnimation, \
                                    TemporaryAnimation, \
                                    StateAnimation
from app.assets.frames import SingleFrame, \
                                    IterableFrame, \
                                    StateFrame
from app.models.state import AnimatorState, \
                                    ContainerState, \
                                    DoorState, \
                                    SwitchState, \
                                    MetricState, \
                                    MultiplierState,\
                                    PositionalState, \
                                    PixieState, \
                                    SpriteState
from app.models.properties import EffectProperties, \
                                    CursorProperties, \
                                    ObjectProperties, \
                                    TileProperties, \
                                    PixieProperties, \
                                    SpriteProperties
class Factory:

    @staticmethod
    def frame(recipe):
        if recipe.frame == "single":
            return SingleFrame()
        if recipe.frame == "iterable":
            return IterableFrame
        if recipe.frame == "state":
            return StateFrame()
        return SingleFrame()

    @staticmethod
    def animation(recipe):
        if recipe.animation == "binary":
            return BinaryAnimation()
        if recipe.animation == "persistent":
            return PersistentAnimation()
        if recipe.animation == "temporary":
            return TemporaryAnimation()
        if recipe.animation == "state":
            return StateAnimation()
        return PersistentAnimation()

    @staticmethod
    def properties(category, snapshot):
        if category == "tiles":
            return TileProperties(**snapshot)
        if category == "effects":
            return EffectProperties(**snapshot)
        if category == "objects":
            return ObjectProperties(**snapshot)
        if category == "cursors":
            return CursorProperties(**snapshot)
        if category == "pixies":
            return PixieProperties(**snapshot)
        if category == "sprites":
            return SpriteProperties(**snapshot)
        return TileProperties(**snapshot)

    @staticmethod
    def state(instance, snapshot):
        if instance == "multipler":
            return MultiplierState(**snapshot)
        if instance == "positional":
            return PositionalState(**snapshot)
        if instance == "metric":
            return MetricState(**snapshot)
        if instance == "animator":
            return AnimatorState(**snapshot)
        if instance == "container":
            return ContainerState(**snapshot)
        if instance == "door":
            return DoorState(**snapshot)
        if instance == "switch":
            return SwitchState(**snapshot)
        if instance == "pixie":
            return PixieState(**snapshot)
        if instance == "sprite":
            return SpriteState(**snapshot)
        return PositionalState(**snapshot)
