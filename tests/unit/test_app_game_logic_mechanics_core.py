"""
# Ontology: tests.unit.test_app_game_mechanics_core

Unit tests for core engine mechanics including Animation and Garbage Collection.
"""
from unittest.mock import Mock, MagicMock
import collections
from app.game.logic.mechanics.core import AnimationMechanics, RemoveMechanics
from app.config.enums import AssetInstances, AssetCategories, Lifecycles
from app.models.state import DevicePayload, MenuPayload, WorldPayload
from app.assets.base import Animation
from app.assets.animations import LifecycleAnimation

def test_animation_mechanics_update():
    """
    Ensure the animate() interface is correctly invoked on the Animation
    components of all targeted Asset Categories and Instances, and cooldown()
    is processed for active Reactable effects.
    """
    board = MagicMock()
    mechanic = AnimationMechanics()
    payload = DevicePayload(menu=MenuPayload(), world=WorldPayload())

    def make_asset(cat, inst):
        a = MagicMock()
        a.category = getattr(cat, 'value', cat)
        a.instance = getattr(inst, 'value', inst)
        
        a.taxonomy = MagicMock()
        a.taxonomy.category = a.category
        a.taxonomy.instance = a.instance
        
        a.state = MagicMock()
        a.state.mutators.triggers.animated = True
        a.state.active = True
        
        a.animation = MagicMock(spec=Animation)
        return a

    effect_asset = make_asset(AssetCategories.EFFECTS, AssetInstances.PASSIVE)
    sheet_asset = make_asset(AssetCategories.SHEETS, AssetInstances.SPRITES)
    chest_asset = make_asset(AssetCategories.OBJECTS, AssetInstances.CHESTS)
    gate_asset = make_asset(AssetCategories.OBJECTS, AssetInstances.GATES)
    plate_asset = make_asset(AssetCategories.OBJECTS, AssetInstances.PLATES)
    
    reactable_asset = make_asset(AssetCategories.EFFECTS, AssetInstances.REACTABLES)
    reactable_asset.animation = MagicMock(spec=LifecycleAnimation)

    assets = [effect_asset, sheet_asset, chest_asset, gate_asset, plate_asset, reactable_asset]

    board.paused = False
    board.assets.return_value = assets
    board.renderables.return_value = assets
    board.layers.return_value = ["0"]

    def mock_categories(cat, layer=None):
        val = getattr(cat, 'value', cat)
        return [a for a in assets if a.category == val]
        
    def mock_instances(inst, layer=None):
        val = getattr(inst, 'value', inst)
        return [a for a in assets if a.instance == val]

    board.categories.side_effect = mock_categories
    board.instances.side_effect = mock_instances

    mechanic.update(board, 0.016, collections.deque(), payload)

    effect_asset.animation.animate.assert_called_once_with(effect_asset.state, effect_asset.properties)
    sheet_asset.animation.animate.assert_called_once_with(sheet_asset.state, sheet_asset.properties)
    chest_asset.animation.animate.assert_called_once_with(chest_asset.state, chest_asset.properties)
    gate_asset.animation.animate.assert_called_once_with(gate_asset.state, gate_asset.properties)
    plate_asset.animation.animate.assert_called_once_with(plate_asset.state, plate_asset.properties)
    reactable_asset.animation.cooldown.assert_called_once_with(reactable_asset.state, reactable_asset.properties)


def test_remove_mechanics_update():
    board = Mock()
    mechanic = RemoveMechanics()
    payload = DevicePayload(menu=MenuPayload(), world=WorldPayload())

    temp_effect_remove = Mock()
    temp_effect_remove.state.animation.frame = 10
    temp_effect_remove.properties.count = 5
    temp_effect_remove.properties.lifecycle.persist = False
    temp_effect_remove.properties.lifecycle.type = Lifecycles.TEMPORARY.value

    temp_effect_keep = Mock()
    temp_effect_keep.state.animation.frame = 2
    temp_effect_keep.properties.count = 5
    temp_effect_keep.properties.lifecycle.persist = False
    temp_effect_keep.properties.lifecycle.type = Lifecycles.TEMPORARY.value

    persist_effect_keep = Mock()
    persist_effect_keep.state.animation.frame = 10
    persist_effect_keep.properties.count = 5
    persist_effect_keep.properties.lifecycle.persist = True
    persist_effect_keep.properties.lifecycle.type = Lifecycles.TEMPORARY.value

    continuous_effect_keep = Mock()
    continuous_effect_keep.state.animation.frame = 10
    continuous_effect_keep.properties.count = 5
    continuous_effect_keep.properties.lifecycle.persist = False
    continuous_effect_keep.properties.lifecycle.type = Lifecycles.CONTINUOUS.value

    dead_sprite = Mock()
    dead_sprite.state.mutators.triggers.dead = True

    alive_sprite = Mock()
    alive_sprite.state.mutators.triggers.dead = False

    board.categories.side_effect = lambda cat: (
        [temp_effect_remove, temp_effect_keep, persist_effect_keep, continuous_effect_keep]
        if cat == AssetCategories.EFFECTS else []
    )
    board.instances.side_effect = lambda inst, *args, **kwargs: (
        [dead_sprite, alive_sprite] if inst == AssetInstances.SPRITES else []
    )

    mechanic.update(board, 0.016, collections.deque(), payload)

    board.remove.assert_called_once_with([temp_effect_remove, dead_sprite])