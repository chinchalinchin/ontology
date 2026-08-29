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
        if getattr(state, 'inventory', None) and getattr(state.inventory, 'equipment', None):
            weapon = state.inventory.equipment.weapon

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
    
        elif intention in (Intentions.WANDER, Intentions.FIND):
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