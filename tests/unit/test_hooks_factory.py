"""
# Ontology: tests.unit.test_hooks_factory
"""
from app.hooks.factory import Factory
from app.config.enums import FrameRecipe, AnimationRecipe, Devices, Mechanics
from app.assets.frames import SpriteFrame, SingleFrame, IterableFrame, NoFrame
from app.assets.animations import PersistentAnimation, BinaryAnimation, NoAnimation
from app.game.devices import Keyboard
from app.game.logic.mechanics import AnimationMechanics, PlayerMechanics
from app.models.config import Mapping

def test_factory_frame():
    assert isinstance(Factory.frame(FrameRecipe.SPRITE), SpriteFrame)
    assert isinstance(Factory.frame(FrameRecipe.SINGLE), SingleFrame)
    assert isinstance(Factory.frame(FrameRecipe.ITERABLE), IterableFrame)
    assert isinstance(Factory.frame(FrameRecipe.NONE), NoFrame)

def test_factory_animation():
    assert isinstance(Factory.animation(AnimationRecipe.PERSISTENT), PersistentAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.BINARY), BinaryAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.NONE), NoAnimation)

def test_factory_taxonomy():
    tax = Factory.taxonomy(
        id="frame-brick", 
        name="house", 
        category="crafts", 
        instance="struts"
    )
    assert tax.id == "frame-brick"
    assert tax.name == "house"
    assert tax.category == "crafts"
    assert tax.instance == "struts"

def test_factory_device():
    device = Factory.device(Devices.KEYBOARD, Mapping())
    assert isinstance(device, Keyboard)

def test_factory_mechanics():
    mechanic_anim = Factory.mechanics(Mechanics.ANIMATION)
    mechanic_player = Factory.mechanics(Mechanics.PLAYER)
    
    assert isinstance(mechanic_anim, AnimationMechanics)
    assert isinstance(mechanic_player, PlayerMechanics)