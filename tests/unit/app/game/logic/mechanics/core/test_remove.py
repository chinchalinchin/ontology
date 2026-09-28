"""
# Ontology: tests.unit.app.game.logic.mechanics.core.test_remove

Unit tests for Garbage Collection mechanics.
"""
# Standard Libraries
from unittest.mock import Mock
import collections

# Application Libraries
from app.game.logic.mechanics.core import  RemoveMechanics
from app.config.enums import (
    AssetInstances, 
    AssetCategories, 
    Lifecycles
)
from app.models.state import (
    DevicePayload, 
    MenuPayload, 
    WorldPayload
)

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