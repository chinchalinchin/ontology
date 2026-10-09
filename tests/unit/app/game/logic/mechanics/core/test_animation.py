"""
# Ontology: tests.unit.app.game.logic.mechanics.core.test_animation
"""
# Standard Libraries
import collections
from unittest.mock import patch, call, MagicMock

# External Libraries
import pytest

# Application Libraries
from app.assets.animations import SpriteAnimation, BinaryAnimation
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

    sheets = mock_board.categories(AssetCategories.SHEETS)
    chests = mock_board.instances(AssetInstances.CHESTS)
    gates = mock_board.instances(AssetInstances.GATES)
    plates = mock_board.instances(AssetInstances.PLATES)
    reactables = mock_board.instances(AssetInstances.REACTABLES.value)

    assert len(sheets) > 0
    assert len(chests) > 0
    assert len(gates) > 0
    assert len(plates) > 0
    assert len(reactables) > 0

    for effect in reactables:
        effect.state.active = True

    binary_assets = chests + gates + plates
    reactable_anim_cls = type(reactables[0].animation)

    with patch.object(SpriteAnimation, "animate") as mock_sprite_anim, \
         patch.object(BinaryAnimation, "animate") as mock_binary_anim, \
         patch.object(reactable_anim_cls, "cooldown") as mock_cooldown:

        # Execute Mechanics
        mechanic.update(mock_board, 0.016, collections.deque(), payload)

        # Assert SpriteAnimation calls
        assert mock_sprite_anim.call_count == len(sheets)
        mock_sprite_anim.assert_has_calls(
            [call(sheet.state, sheet.properties) for sheet in sheets],
            any_order=True
        )

        # Assert BinaryAnimation calls across chests, gates, and plates
        assert mock_binary_anim.call_count == len(binary_assets)
        mock_binary_anim.assert_has_calls(
            [call(asset.state, asset.properties) for asset in binary_assets],
            any_order=True
        )

        # Assert Cooldown calls for Reactables
        assert mock_cooldown.call_count == len(reactables)
        mock_cooldown.assert_has_calls(
            [call(effect.state, effect.properties) for effect in reactables],
            any_order=True
        )