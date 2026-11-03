"""
# Ontology: tests.unit.app.game.logic.mechanics.core.test_remove

Unit tests for Garbage Collection mechanics.
"""
# Standard Libraries
from unittest.mock import Mock
import collections

# Application Libraries
from app.game.logic.mechanics.core import  RemoveMechanics
from app.static.semantics import (
    AssetInstances, 
    AssetCategories, 
    Frequencies
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
    temp_effect_remove.properties.frequency.persist = False
    temp_effect_remove.properties.frequency.type = Frequencies.TEMPORARY.value

    temp_effect_keep = Mock()
    temp_effect_keep.state.animation.frame = 2
    temp_effect_keep.properties.count = 5
    temp_effect_keep.properties.frequency.persist = False
    temp_effect_keep.properties.frequency.type = Frequencies.TEMPORARY.value

    persist_effect_keep = Mock()
    persist_effect_keep.state.animation.frame = 10
    persist_effect_keep.properties.count = 5
    persist_effect_keep.properties.frequency.persist = True
    persist_effect_keep.properties.frequency.type = Frequencies.TEMPORARY.value

    continuous_effect_keep = Mock()
    continuous_effect_keep.state.animation.frame = 10
    continuous_effect_keep.properties.count = 5
    continuous_effect_keep.properties.frequency.persist = False
    continuous_effect_keep.properties.frequency.type = Frequencies.CONTINUOUS.value

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