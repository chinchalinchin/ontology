# /home/grant/Projects/ontology/tests/unit/test_app_game_mechanics_core.py

"""
# Ontology: tests.unit.test_app_game_mechanics_core

Unit tests for core engine mechanics including Animation and Garbage Collection.
"""
from unittest.mock import Mock
import collections
from app.game.logic.mechanics.core import AnimationMechanics, RemoveMechanics
from app.config.enums import AssetCategories, AssetInstances

def test_animation_mechanics_update():
    """
    Ensure the animate() interface is correctly invoked on the Animation 
    components of all targeted Asset Categories and Instances.
    """
    board = Mock()
    mechanic = AnimationMechanics()

    # Create mock assets for each category/instance
    effect_asset = Mock()
    sheet_asset = Mock()
    chest_asset = Mock()
    gate_asset = Mock()
    plate_asset = Mock()

    def mock_categories(cat):
        if cat == AssetCategories.EFFECTS:
            return [effect_asset]
        if cat == AssetCategories.SHEETS:
            return [sheet_asset]
        return []

    def mock_instances(inst):
        if inst == AssetInstances.CHESTS:
            return [chest_asset]
        if inst == AssetInstances.GATES:
            return [gate_asset]
        if inst == AssetInstances.PLATES:
            return [plate_asset]
        return []

    board.categories.side_effect = mock_categories
    board.instances.side_effect = mock_instances

    mechanic.update(board, 0.016, collections.deque())

    # Verify animate() is called on the targeted assets with their respective state and properties
    effect_asset.animation.animate.assert_called_once_with(effect_asset.state, effect_asset.properties)
    sheet_asset.animation.animate.assert_called_once_with(sheet_asset.state, sheet_asset.properties)
    chest_asset.animation.animate.assert_called_once_with(chest_asset.state, chest_asset.properties)
    gate_asset.animation.animate.assert_called_once_with(gate_asset.state, gate_asset.properties)
    plate_asset.animation.animate.assert_called_once_with(plate_asset.state, plate_asset.properties)

def test_remove_mechanics_update():
    """
    Ensure that temporary effects exceeding their frame count and dead sprites 
    are properly identified and submitted to the Board for garbage collection.
    """
    board = Mock()
    mechanic = RemoveMechanics()

    # Temporary Effects
    temp_effect_remove = Mock()
    temp_effect_remove.state.animation.frame = 10
    temp_effect_remove.properties.count = 5 # Frame > count -> Should be removed

    temp_effect_keep = Mock()
    temp_effect_keep.state.animation.frame = 2
    temp_effect_keep.properties.count = 5 # Frame < count -> Should be kept

    # Sprites
    dead_sprite = Mock()
    dead_sprite.state.mutators.triggers.dead = True # Dead -> Should be removed

    alive_sprite = Mock()
    alive_sprite.state.mutators.triggers.dead = False # Alive -> Should be kept

    def mock_instances(inst):
        if inst == AssetInstances.TEMPORARY:
            return [temp_effect_remove, temp_effect_keep]
        if inst == AssetInstances.SPRITES:
            return [dead_sprite, alive_sprite]
        return []

    board.instances.side_effect = mock_instances

    mechanic.update(board, 0.016, collections.deque())

    # Verify that only the completed effect and the dead sprite were flagged for removal
    board.remove.assert_called_once_with([temp_effect_remove, dead_sprite])