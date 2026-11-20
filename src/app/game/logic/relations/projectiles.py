"""
@domain.logic
@app.module
@app.relation
@workflow.projectiles

# Ontology: Source - app.game.logic.relations.projectiles

Relational index mapping Projectiles and Weapons.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Dict,
    Optional,
    TYPE_CHECKING
)
import logging

# Application Libraries
from app.models.abstracts import Singleton

if TYPE_CHECKING:
    from app.models.properties import CursorProperties

# ---------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------


class ProjectileIndex(Singleton):
    """
    Compiled relational index mapping Weapon Asset IDs to Projectile Asset IDs.
    """
    _map: Dict[str, str] = {}

    def __init__(self, relations: Optional[Dict[str, str]] = None):
        self._map = {}
        if relations:
            for weapon_id, projectile_id in relations.items():
                self.register(weapon_id, projectile_id)

    @classmethod
    def from_properties(
        cls,
        projectiles: Dict[str, CursorProperties]
    ) -> ProjectileIndex:
        """
        Factory constructor compiling weapon-to-projectile relations from
        cursor projectile property schemas.
        """
        index = cls()
        for projectile_id, props in projectiles.items():
            if not props.weapon:
                continue
            index.register(props.weapon, projectile_id)
        return index

    def register(self, weapon_id: str, projectile_id: str) -> None:
        """
        Registers a weapon Asset ID to its emitted projectile Asset ID.
        Raises ValueError on conflicting duplicate weapon bindings.
        """
        existing = self._map.get(weapon_id)
        if existing is not None and existing != projectile_id:
            raise ValueError(
                f"Weapon '{weapon_id}' is already bound to projectile "
                f"'{existing}'; cannot rebind to '{projectile_id}'."
            )
        self._map[weapon_id] = projectile_id

    def resolve(self, weapon_id: Optional[str]) -> Optional[str]:
        """
        Resolves the projectile Asset ID bound to the given weapon ID.
        """
        if not weapon_id:
            return None
        return self._map.get(weapon_id)