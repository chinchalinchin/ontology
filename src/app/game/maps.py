"""
# Ontology: Resolvers
"""
# Application Libraries
from app.config.enums import Actions, Directions, Intentions

# Cython Libraries
from libs.core import Position

class AnimationMap:

    @staticmethod
    def action(state, equipment_properties) -> Actions:
        """
        Resolves Sprite Dispositions to Animation Actions.

        - state: sprite state
        - equipment: equipment properties
        """
        weapon = state.inventory.equipment.weapon
        tool = state.inventory.equipment.tool
        utility = state.inventory.equipment.utility
        armor = state.inventory.equipment.armor
        disposition = state.intention.disposition

        if state.intention == Intentions.ATTACK:
            if not weapon:
                return Actions.CAST  # Default fallback for unarmed/magic attacks
            
            # TODO: handle `all`
            return equipment_properties["weapons"][weapon].animation
    
        elif state.intention in [Intentions.WANDER, Intentions.FIND]:
            return Actions.WALK

        return Actions.WALK

    @staticmethod
    def direction(position: Position, target: Position) -> Directions:
        dx = target.x - position.x
        dy = target.y - position.y
    
        # In graphics coordinates, larger y is physically lower.
        if dy > dx:
            # Lower than both diagonals means it is physically DOWN
            return Directions.DOWN if dy > -dx else Directions.LEFT
        
        # Higher than both diagonals means it is physically UP
        return Directions.RIGHT if dy > -dx else Directions.UP