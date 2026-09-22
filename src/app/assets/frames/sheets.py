"""
# Ontology: app.assets.frames.sheets

Package for Sheet Frame implementations.
"""
# Stamdard Libraries
from typing import (
    List,
    Tuple,
)
import logging

# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    Intentions,
    RequiredAssets,
    ExpressionsPalette,
    ChannelTypes
)
from app.assets.base import Frame
from app.models.state import (
    AssetState, 
    SpriteState
)
from app.models.properties import (
    AssetProperties,
    SheetProperties,
)

logger = logging.getLogger(__name__)

class StateFrame(Frame):
    """
    ## StateFrame
    """

    def channels(self, 
        id: str, 
        state: AssetState,
        properties: AssetProperties
    ) -> List[Tuple]:
        return []

    
    def keys(self, id: str, state: AssetState) -> List[str]:
        """
        """
        return [(settings.SEPARATOR.join([
            id, 
            state.animation.action, 
            state.animation.direction,
            str(state.animation.frame)
        ]), 0, 0)]


    def index(self, id: str, properties: SheetProperties) -> dict[str, tuple[int, int, int, int]]:
        """
        """
        w = properties.dimensions.w
        l = properties.dimensions.l
        crops = {}

        properties.actions
        # Handle dict format since this goes through dataclasses.asdict()
        for action, action_prop in properties.actions.items():
            for direction, dir_prop in action_prop.directions.items():
                row = dir_prop.row 
                count = action_prop.count
                for f in range(count):
                    frame_key = settings.SEPARATOR.join([
                        id,
                        action,
                        direction,
                        str(f)
                    ])
                    crops[frame_key] = (f * w, row * l, w, l)
        return crops

# -------------------------------------------------------------------------------------

class SpriteFrame(StateFrame):
    """
    ## SpriteFrame

    Specialized Frame component for Sprites that yields a strict Z-indexed list of frame keys based on the Sprite's inventory.
    """

    def channels(self, 
        id: str, 
        state: SpriteState,
        properties: SheetProperties
    ) -> List[Tuple]:
        channel_directives = []
        
        if state.mutators.triggers.submerged:
            l = properties.dimensions.l
            half_l = l // 2
            
            # (CHANNEL_SUBMERGE, split_y, r, g, b, a)
            # e.g., deep aquatic modulation: RGBA(40, 110, 180, 170)
            # TODO: this should be codified in a ChannelPayload data structure to pass to the screen. Screen should unpack channel payload into Cython primitives.            
            payload = half_l, 40, 110, 180, 170
            channel_directives.append((
                ChannelTypes.SUBMERGE.value,
                payload
            ))
            
        return channel_directives

    
    def keys(self, id: str, state: SpriteState) -> List[str]:
        # Start with the base Persona frame key
        frame_keys = super().keys(id, state)
        
        # Iterate over active equipment in strict Z-index order: Base -> Armor -> Utility -> Tool -> Weapon
        if state.inventory.equipment:
            eq = state.inventory.equipment
            for eq_key in (eq.armor, eq.utility, eq.tool, eq.weapon, eq.shield):
                if eq_key:
                    key_str = settings.SEPARATOR.join([
                        eq_key,
                        state.animation.action,
                        state.animation.direction,
                        str(state.animation.frame)
                    ])
                    frame_keys.append((key_str, 0, 0))

        if id != RequiredAssets.PLAYER.value and state.psyche.expression:
            expr = state.psyche.expression
            expr_key = settings.SEPARATOR.join([
                ExpressionsPalette.BUBBLES.value,
                state.psyche.expression.icon
            ])
            frame_keys.append((expr_key, expr.offset.x, expr.offset.y))
            
        if state.intention is not None and state.intention == Intentions.ATTACK:
            logger.info(f"SpriteFrame generated keys: {frame_keys}")
        
        return frame_keys