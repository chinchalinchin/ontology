"""
# Ontology: Resolvers
"""
# Application Libraries
from app.config.enums import Actions, Dispositions

class DispositionResolver:

    @staticmethod
    def action(state, equipment) -> Actions:
        """
        Resolves Sprite Dispositions to Animation Actions.
        """
        weapon = state.inventory.equipment.weapon
        tool = state.inventory.equipment.tool
        utility = state.inventory.equipment.utility
        armor = state.inventory.equipment.armor

        if state.intention.disposition in [Dispositions.ATTACK, Dispositions.HUNT]:
            if not weapon:
                return Actions.CAST  # Default fallback for unarmed/magic attacks
            
            # TODO: handle `all`
            return equipment["weapons"][weapon].animation
    
        elif state.intention.disposition == Dispositions.CONSTRUCT:
            if not tool:
                return Actions.WALK  # Default fallback for empty hands
    
            # TODO: handle `all`
            return equipment["tools"][tool].animation
        
        elif state.intention.disposition in [Dispositions.WANDER, Dispositions.FIND]:
            return Actions.WALK

        return Actions.WALK