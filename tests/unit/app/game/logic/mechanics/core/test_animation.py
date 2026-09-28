"""
# Ontology: tests.unit.app.game.logic.mechanics.core.test_animation
"""
# Standard Libraries
import collections
from unittest.mock import MagicMock

# External Libraries
import pytest

# Application Libraries
from app.game.logic.mechanics import AnimationMechanics
from app.config.enums import AssetCategories, AssetInstances
from app.models.state import DevicePayload


@pytest.mark.animations
def test_animation_mechanics_update(mock_board):
    """
    Ensure the animate() interface is correctly invoked on the Animation
    components of all targeted Asset Categories and Instances, and cooldown()
    is processed for active Reactable effects.
    """
    mechanic = AnimationMechanics()
    payload = MagicMock(spec=DevicePayload)

    mock_board.paused = False

    # Gather target assets directly via the exact Board query methods AnimationMechanics uses
    effects = mock_board.categories(AssetCategories.EFFECTS)
    sheets = mock_board.categories(AssetCategories.SHEETS)
    chests = mock_board.instances(AssetInstances.CHESTS)
    gates = mock_board.instances(AssetInstances.GATES)
    plates = mock_board.instances(AssetInstances.PLATES)
    reactables = mock_board.instances(AssetInstances.REACTABLES.value)

    # Verify our testbed successfully hydrated these specific fixture categories
    assert len(effects) > 0, "No Effect fixtures found on the board."
    assert len(sheets) > 0, "No Sheet fixtures found on the board."
    assert len(chests) > 0, "No Chest fixtures found on the board."
    assert len(gates) > 0, "No Gate fixtures found on the board."
    assert len(plates) > 0, "No Plate fixtures found on the board."
    assert len(reactables) > 0, "No Reactable fixtures found on the board."

    # Spy on the animation methods to verify execution without stubbing the entire object
    all_animating_assets = effects + sheets + chests + gates + plates
    for asset in all_animating_assets:
        asset.animation.animate = MagicMock()
        
    for effect in reactables:
        # Force active to True to trigger the cooldown path 
        effect.state.active = True
        effect.animation.cooldown = MagicMock()

    # Execute Mechanics
    mechanic.update(mock_board, 0.016, collections.deque(), payload)

    # Assert calls
    for asset in all_animating_assets:
        asset.animation.animate.assert_called_once_with(asset.state, asset.properties)

    for effect in reactables:
        effect.animation.cooldown.assert_called_once_with(effect.state, effect.properties)