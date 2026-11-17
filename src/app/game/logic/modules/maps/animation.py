"""
@domain.logic
@app.module
@modality.intention
@workflow.combat

# Ontology: Source - app.game.maps.animation

Animation Maps for mapping SpriteState to Equipment Frames.
"""
# Application Libraries
from app.static.semantics import (
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
        weapon = state.slots.equipment.weapon
        tool = state.slots.equipment.tool
        utility = state.slots.equipment.utility
        intention = state.intention

        if intention in StaticIntentions:
            return Actions.WALK.value

        if intention == Intentions.ATTACK.value:
            if not weapon:
                return Actions.CAST.value # Default
            
            weapon_asset = equipment.weapons.get(weapon)

            if weapon_asset and weapon_asset.properties.actions:
                return next(iter(weapon_asset.properties.actions))
            
            return Actions.CAST.value
    
        if intention == Intentions.MINE.value:
            if not tool:
                return Actions.THRUST.value # Default mining action fallback
            
            tool_asset = equipment.tools.get(tool)
            
            if tool_asset and tool_asset.properties.actions:
                return next(iter(tool_asset.properties.actions))
                
            return Actions.THRUST.value

        if intention == Intentions.BUILD.value:
            if not utility:
                return Actions.CAST.value # Default build action fallback
            
            utility_asset = equipment.utilities.get(utility)
            
            if utility_asset and utility_asset.properties.actions:
                return next(iter(utility_asset.properties.actions))
                
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