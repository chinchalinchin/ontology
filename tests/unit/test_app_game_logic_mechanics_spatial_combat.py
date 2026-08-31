"""
# Ontology: tests.unit.test_app_game_logic_mechanics_spatial_combat.py
"""
import pytest
from unittest.mock import MagicMock, patch

from app.game.logic.mechanics.spatial.combat import CombatMechanics
from app.config.enums import Intentions, AssetInstances
from libs.core.models import Position, Dimensions, Hitbox

def _setup_target():
    target = MagicMock()
    target.name = "enemy"
    target.instance = AssetInstances.SPRITES
    target.state.mutators.triggers.dead = False
    target.state.mutators.triggers.struck = False
    target.dimensions = Dimensions(32, 32)
    target.hitboxes = [Hitbox(Position(0,0), Dimensions(32, 32))]
    target.state.position = Position(15, 15)
    return target

def test_combat_mechanics_melee_resolution(mock_board):
    mechanic = CombatMechanics()
    
    attacker = mock_board.player()
    attacker.state.intention = Intentions.ATTACK
    attacker.state.character = MagicMock(strength=20)
    attacker.state.animation.action = "slash"
    
    # PATCH: Modify the underlying properties object, not the computed getter
    attacker.properties.dimensions = Dimensions(32, 32)
    attacker.properties.hitboxes = [Hitbox(Position(0,0), Dimensions(32, 32))]
    attacker.state.position = Position(10, 10)
    
    target = _setup_target()
    target.state.character.defense = 5
    target.state.meters.health.current = 50
    
    mock_board.instances = lambda inst, layer=None: [attacker] if inst == AssetInstances.PLAYERS else [target]
    
    # Patch collisions to assume broad-phase correctly flagged the overlap
    with patch.object(mechanic, 'collisions', return_value=[(attacker, target)]):
        # We let the native Cython Geometry.intersects calculate the overlap
        mechanic.update(mock_board, 0.16, MagicMock(), MagicMock())
    
    # 20 strength - 5 defense = 15 damage. Health should drop from 50 to 35.
    assert target.state.meters.health.current == 35
    assert target.state.mutators.triggers.struck is True
    assert target.state.mutators.triggers.dead is False

def test_combat_mechanics_lethal_blow(mock_board):
    mechanic = CombatMechanics()
    
    attacker = mock_board.player()
    attacker.state.intention = Intentions.ATTACK
    attacker.state.character = MagicMock(strength=100) # Ensure overwhelming damage
    attacker.state.animation.action = "slash"
    
    # PATCH: Modify the underlying properties object, not the computed getter
    attacker.properties.dimensions = Dimensions(32, 32)
    attacker.properties.hitboxes = [Hitbox(Position(0,0), Dimensions(32, 32))]
    attacker.state.position = Position(10, 10)
    
    target = _setup_target()
    target.state.character.defense = 0
    target.state.meters.health.current = 10
    
    mock_board.instances = lambda inst, layer=None: [attacker] if inst == AssetInstances.PLAYERS else [target]
    
    with patch.object(mechanic, 'collisions', return_value=[(attacker, target)]):
        # We let the native Cython Geometry.intersects calculate the overlap
        mechanic.update(mock_board, 0.16, MagicMock(), MagicMock())
    
    # 100 damage vs 10 health -> trigger death state
    assert target.state.meters.health.current == 0
    assert target.state.mutators.triggers.dead is True