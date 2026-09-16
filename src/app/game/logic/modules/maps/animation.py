"""
# Ontology: app.game.maps
"""
# Application Libraries
import app.config.settings as settings
from app.config.enums import (
    Actions, 
    Directions, 
    Intentions,
    StaticIntentions
)
from app.models.groups import EquipmentGroup
from app.models.state import (
    SpriteState
)

# Cython Libraries
from libs.core.models import Position

class AnimationMap:
    """
    """

    @staticmethod
    def action(state: SpriteState, equipment: EquipmentGroup) -> Actions:
        """
        Resolves Sprite Intentions to Animation Actions.

        - state: sprite state
        - equipment: equipment properties
        """
        weapon = state.inventory.equipment.weapon
        tool = state.inventory.equipment.tool
        utility = state.inventory.equipment.utility
        intention = state.intention

        if intention in StaticIntentions:
            return Actions.WALK.value

        if intention == Intentions.ATTACK.value:
            if not weapon:
                return Actions.CAST.value # Default
            
            weapon_property = equipment.weapons.get(weapon)

            if weapon_property and weapon_property.actions:
                return next(iter(weapon_property.actions))
            
            return Actions.CAST.value
    
        if intention == Intentions.MINE.value:
            if not tool:
                return Actions.THRUST.value # Default mining action fallback
            
            tool_property = equipment.tools.get(tool)
            
            if tool_property and tool_property.actions:
                return next(iter(tool_property.actions))
                
            return Actions.THRUST.value

        if intention == Intentions.BUILD.value:
            if not utility:
                return Actions.CAST.value # Default build action fallback
            
            utility_property = equipment.utilities.get(utility)
            
            if utility_property and utility_property.actions:
                return next(iter(utility_property.actions))
                
            return Actions.CAST.value

        if intention in (
            Intentions.INTERACT.value,
            Intentions.WANDER, 
            Intentions.FIND, 
            Intentions.FOLLOW, 
            Intentions.HUNT, 
            Intentions.ESCAPE, 
            Intentions.RETURN
        ):
            return Actions.WALK.value

        return Actions.WALK.value
    

    @staticmethod
    def direction(position: Position, target: Position) -> str:
        dx = target.x - position.x
        dy = target.y - position.y
    
        # In graphics coordinates, larger y is physically lower.
        if dy > dx:
            # Lower than both diagonals means it is physically DOWN
            return Directions.DOWN.value if dy > -dx else Directions.LEFT.value
        
        # Higher than both diagonals means it is physically UP
        return Directions.RIGHT.value if dy > -dx else Directions.UP.value

    @staticmethod
    def attackbox(sprite: SpriteState, equipment: EquipmentGroup):
        frame_key = settings.SEPARATOR.join([
            sprite.state.animation.action,
            sprite.state.animation.direction,
            sprite.state.animation.frame
        ])
        weapon_key = sprite.state.inventory.equipment.weapon
        weapon_props = equipment.weapons.get(weapon_key,{}).attackboxes.get(frame_key)

