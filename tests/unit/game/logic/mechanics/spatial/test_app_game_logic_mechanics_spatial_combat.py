"""
# Ontology: tests.unit.test_app_game_logic_mechanics_spatial_combat.py
"""
import pytest
from unittest.mock import MagicMock

from app.game.logic.mechanics.spatial.combat import CombatMechanics
from app.config.enums import Intentions, AssetInstances, AssetCategories
from libs.core.models import Position, Dimensions, Hitbox
from app.assets.base import Asset, Taxonomy
from app.models.properties import SheetProperties, EffectProperties, Lifecycle
from app.models.state import (
    SpriteState, 
    PlayerState, 
    Character, 
    Meters, 
    Meter, 
    Mutators, 
    MutatorTriggers, 
    AnimationState, 
    ReactableState
)
from app.models.groups import EquipmentGroup
from tests.unit.conftest import DummyFrame, DummyAnimation


def _create_player_attacker(x=10, y=10, action="slash", direction="right", frame=3, strength=20):
    tax = Taxonomy("player-1", "hero", AssetCategories.SHEETS.value, AssetInstances.PLAYERS.value)
    props = SheetProperties(dimensions=Dimensions(w=64, l=64), mass=10)
    state = PlayerState(
        id="player-1",
        name="hero",
        layer="0",
        position=Position(x=x, y=y),
        character=Character(strength=strength, defense=10, speed=5),
        meters=Meters(health=Meter(current=100, maximum=100), magic=Meter(current=100, maximum=100)),
        mutators=Mutators(triggers=MutatorTriggers()),
        animation=AnimationState(action=action, direction=direction, frame=frame),
        intention=Intentions.ATTACK
    )
    state.inventory.equipment.weapon = "shortsword"
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


def _create_sprite_target(x=50, y=20, defense=5, health=50):
    tax = Taxonomy("enemy-1", "enemy", AssetCategories.SHEETS.value, AssetInstances.SPRITES.value)
    props = SheetProperties(
        dimensions=Dimensions(w=64, l=64),
        mass=10,
        hitboxes=[Hitbox(Position(0, 0), Dimensions(32, 32))]
    )
    state = SpriteState(
        id="enemy-1",
        name="enemy",
        layer="0",
        position=Position(x=x, y=y),
        character=Character(strength=10, defense=defense, speed=5),
        meters=Meters(health=Meter(current=health, maximum=health), magic=Meter(current=50, maximum=50)),
        mutators=Mutators(triggers=MutatorTriggers(dead=False)),
        animation=AnimationState(frame=0, tick=0)
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


def _create_reactable_target(x=50, y=20):
    tax = Taxonomy("dummy-1", "test-dummy", AssetCategories.EFFECTS.value, AssetInstances.REACTABLES.value)
    props = EffectProperties(
        dimensions=Dimensions(w=64, l=64),
        count=8,
        lifecycle=Lifecycle(type="temporary", persist=True),
        mass=0,
        hitboxes=[Hitbox(Position(0, 0), Dimensions(64, 64))]
    )
    state = ReactableState(
        id="dummy-1",
        name="test-dummy",
        layer="0",
        position=Position(x=x, y=y),
        intention=Intentions.ATTACK.value,
        active=False
    )
    return Asset(tax, props, state, DummyFrame(), DummyAnimation())


def _create_equipment():
    shortsword_props = SheetProperties(
        dimensions=Dimensions(w=64, l=64),
        attackboxes={
            "slash-right-3": [Hitbox(Position(40, 16), Dimensions(24, 32))]
        }
    )
    return EquipmentGroup(
        armor={},
        tools={},
        utilities={},
        weapons={"shortsword": shortsword_props}
    )


def test_combat_mechanics_melee_resolution(mock_board):
    mechanic = CombatMechanics()
    attacker = _create_player_attacker(x=10, y=10, strength=20)
    target = _create_sprite_target(x=50, y=20, defense=5, health=50)

    mock_board.equipment = _create_equipment()
    mock_board.layers = lambda: ["0"]
    mock_board.instances = lambda inst, layer=None: [attacker] if inst == AssetInstances.PLAYERS.value else [target]

    mechanic.update(mock_board, 0.016, MagicMock(), MagicMock())

    # Strength 20 - Defense 5 = 15 damage (50 -> 35)
    assert target.state.meters.health.current == 35
    assert target.state.mutators.triggers.dead is False


def test_combat_mechanics_lethal_blow(mock_board):
    mechanic = CombatMechanics()
    attacker = _create_player_attacker(x=10, y=10, strength=100)
    target = _create_sprite_target(x=50, y=20, defense=0, health=10)

    mock_board.equipment = _create_equipment()
    mock_board.layers = lambda: ["0"]
    mock_board.instances = lambda inst, layer=None: [attacker] if inst == AssetInstances.PLAYERS.value else [target]

    mechanic.update(mock_board, 0.016, MagicMock(), MagicMock())

    assert target.state.meters.health.current == 0
    assert target.state.mutators.triggers.dead is True


def test_combat_mechanics_reactable_trigger(mock_board):
    mechanic = CombatMechanics()
    attacker = _create_player_attacker(x=10, y=10)
    dummy = _create_reactable_target(x=50, y=20)

    mock_board.equipment = _create_equipment()
    mock_board.layers = lambda: ["0"]
    
    def mock_instances(inst, layer=None):
        if inst == AssetInstances.PLAYERS.value:
            return [attacker]
        if inst == AssetInstances.REACTABLES.value:
            return [dummy]
        return []

    mock_board.instances = mock_instances

    mechanic.update(mock_board, 0.016, MagicMock(), MagicMock())
    assert dummy.state.active is True


def test_combat_mechanics_inactive_attackbox_filtered(mock_board):
    mechanic = CombatMechanics()
    # Frame 0 has no active attackboxes configured
    attacker = _create_player_attacker(x=10, y=10, frame=0)
    target = _create_sprite_target(x=50, y=20, health=50)

    mock_board.equipment = _create_equipment()
    mock_board.layers = lambda: ["0"]
    mock_board.instances = lambda inst, layer=None: [attacker] if inst == AssetInstances.PLAYERS.value else [target]

    mechanic.update(mock_board, 0.016, MagicMock(), MagicMock())
    assert target.state.meters.health.current == 50


def test_combat_mechanics_unarmed_bypasses_melee(mock_board):
    mechanic = CombatMechanics()
    attacker = _create_player_attacker(x=10, y=10)
    attacker.state.inventory.equipment.weapon = None
    target = _create_sprite_target(x=50, y=20, health=50)

    mock_board.equipment = _create_equipment()
    mock_board.layers = lambda: ["0"]
    mock_board.instances = lambda inst, layer=None: [attacker] if inst == AssetInstances.PLAYERS.value else [target]

    mechanic.update(mock_board, 0.016, MagicMock(), MagicMock())
    assert target.state.meters.health.current == 50