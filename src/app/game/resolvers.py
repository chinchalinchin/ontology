"""
# Ontology: Resolvers
"""
# Application Libraries
from app.config.enums import Actions
from app.models.state import Inventory

class ActionResolver:
    @staticmethod
    def attack(inventory: Inventory, equipment_props: dict) -> str:
        """Resolves an attack intent into a physical animation."""
        weapon = inventory.equipment.weapon
        if not weapon:
            return Actions.CAST  # Default fallback for unarmed/magic attacks

        # TODO: handle `all`
        return equipment_props["weapons"][weapon].animation

    @staticmethod
    def labor(inventory: Inventory, equipment_props: dict) -> str:
        """Resolves a labor intent into a physical animation."""
        tool = inventory.equipment.tool
        if not tool:
            return Actions.WALK  # Default fallback for empty hands

        # TODO: handle `all`
        return equipment_props["tools"][tool].animation