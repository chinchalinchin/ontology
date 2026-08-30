"""
# Ontology: tests.unit.test_app_hooks_factory
"""
from app.services.factory import Factory
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe, 
    Devices, 
    Mechanics,
    Controllers
)
from app.assets.frames import (
    SpriteFrame, 
    SingleFrame, 
    IterableFrame, 
    StateFrame,
    TraversalFrame,
    MeterFrame,
    NoFrame
)
from app.assets.animations import (
    PersistentAnimation, 
    BinaryAnimation,
    TemporaryAnimation,
    StateAnimation,
    TraversalAnimation,
    MeterAnimation,
    NoAnimation
)
from app.game.devices import Keyboard
from app.game.logic.mechanics import (
    AnimationMechanics, 
    PlayerMechanics
)
from app.game.menus.controllers import (
    DisplayController,
    ScrollController
)
from app.models.config import (
    DeviceMapping,
    WorldMapping, 
    MenuMapping
)

def test_factory_frame():
    assert isinstance(Factory.frame(FrameRecipe.SPRITE), SpriteFrame)
    assert isinstance(Factory.frame(FrameRecipe.SINGLE), SingleFrame)
    assert isinstance(Factory.frame(FrameRecipe.ITERABLE), IterableFrame)
    assert isinstance(Factory.frame(FrameRecipe.STATE), StateFrame)
    assert isinstance(Factory.frame(FrameRecipe.TRAVERSAL), TraversalFrame)
    assert isinstance(Factory.frame(FrameRecipe.METER), MeterFrame)
    assert isinstance(Factory.frame(FrameRecipe.NONE), NoFrame)

def test_factory_animation():
    assert isinstance(Factory.animation(AnimationRecipe.PERSISTENT), PersistentAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.BINARY), BinaryAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.TEMPORARY), TemporaryAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.STATE), StateAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.TRAVERSAL), TraversalAnimation)
    assert isinstance(Factory.animation(AnimationRecipe.METER), MeterAnimation)
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
    mapping = DeviceMapping(world=WorldMapping(), menu=MenuMapping())
    device = Factory.device(Devices.KEYBOARD, mapping)
    assert isinstance(device, Keyboard)

def test_factory_mechanics():
    mechanic_anim = Factory.mechanics(Mechanics.ANIMATION)
    mechanic_player = Factory.mechanics(Mechanics.PLAYER)
    
    assert isinstance(mechanic_anim, AnimationMechanics)
    assert isinstance(mechanic_player, PlayerMechanics)

def test_factory_controller():
    ctrl_display = Factory.controller(Controllers.DISPLAY)
    ctrl_scroll = Factory.controller(Controllers.SCROLL)
    
    assert isinstance(ctrl_display, DisplayController)
    assert isinstance(ctrl_scroll, ScrollController)

def test_factory_string_resolution():
    """Verify Factory unboxes Cython strings correctly to their Enum equivalents."""
    from app.services.factory import Factory
    from app.assets.frames import TraversalFrame
    from app.assets.animations import MeterAnimation
    from app.game.logic.mechanics.core import MenuMechanics
    from app.game.menus.controllers.display import DisplayController

    # Test frame fallback
    frame = Factory.frame("traversal")
    assert isinstance(frame, TraversalFrame)
    
    # Test animation fallback
    anim = Factory.animation("meter")
    assert isinstance(anim, MeterAnimation)
    
    # Test mechanics fallback
    mech = Factory.mechanics("menu")
    assert isinstance(mech, MenuMechanics)
    
    # Test controller fallback
    ctrl = Factory.controller("display")
    assert isinstance(ctrl, DisplayController)