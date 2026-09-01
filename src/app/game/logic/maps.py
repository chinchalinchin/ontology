"""
# Ontology: app.game.maps
"""
# Application Libraries
from app.config.enums import Actions, Directions, Intentions

# Cython Libraries
from libs.core.models import Position

class AnimationMap:
    """
    """

    @staticmethod
    def action(state, equipment) -> str:
        """
        Resolves Sprite Intentions to Animation Actions.

        - state: sprite state
        - equipment: equipment properties
        """
        weapon = None
        tool = None
        utility = None
        
        if getattr(state, 'inventory', None) and getattr(state.inventory, 'equipment', None):
            weapon = state.inventory.equipment.weapon
            tool = state.inventory.equipment.tool
            utility = state.inventory.equipment.utility

        intention = state.intention

        if intention == Intentions.IDLE:
            return Actions.WALK

        if intention == Intentions.ATTACK:
            if not weapon:
                return Actions.CAST # Default
            
            weapon_property = equipment.weapons.get(weapon)

            if weapon_property and weapon_property.actions:
                return next(iter(weapon_property.actions))
            
            return Actions.CAST
    
        if intention == Intentions.MINE:
            if not tool:
                return Actions.THRUST # Default mining action fallback
            
            tool_property = equipment.tools.get(tool)
            
            if tool_property and tool_property.actions:
                return next(iter(tool_property.actions))
                
            return Actions.THRUST

        if intention == Intentions.BUILD:
            if not utility:
                return Actions.CAST # Default build action fallback
            
            utility_property = equipment.utilities.get(utility)
            
            if utility_property and utility_property.actions:
                return next(iter(utility_property.actions))
                
            return Actions.CAST
            
        if intention == Intentions.INTERACT:
            return Actions.WALK
            
        if intention in (Intentions.WANDER, Intentions.FIND, Intentions.FOLLOW, Intentions.HUNT, Intentions.ESCAPE, Intentions.RETURN):
            return Actions.WALK

        return Actions.WALK
    

    @staticmethod
    def direction(position: Position, target: Position) -> str:
        dx = target.x - position.x
        dy = target.y - position.y
    
        # In graphics coordinates, larger y is physically lower.
        if dy > dx:
            # Lower than both diagonals means it is physically DOWN
            return Directions.DOWN if dy > -dx else Directions.LEFT
        
        # Higher than both diagonals means it is physically UP
        return Directions.RIGHT if dy > -dx else Directions.UP

class DialogueMap:
    """
    """
    pass