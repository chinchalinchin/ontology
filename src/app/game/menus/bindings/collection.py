"""
# Ontology: app.game.menus.bindings.collection

Package for binding collection data to Gizmo slots.
"""
# Standard Libraries
from typing import Callable, Tuple, Any, List
import logging

# Application Libraries
from app.game.menus.bindings.base import Binding
from app.game.menus.contexts import MenuContext
from app.config.enums import Statuses

logger = logging.getLogger(__name__)


class CollectionBinding(Binding):
    """
    ## CollectionBinding

    Binding component for collection elements (e.g., inventory slots, trade grids).
    Manages dynamic index slicing, pagination offsets, and bounds checking.
    """
    index: int
    offset: int

    def __init__(self, target: dict, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self.index = int(self.target.get("index", 0))
        self.offset = int(self.target.get("offset", 0))

    def _get_collection(self) -> List[Any]:
        """Resolves the live collection from the contextual path."""
        path_key = "source" if "source" in self.resolved else ("collection" if "collection" in self.resolved else None)
        if path_key:
            parent, attr = self.resolved[path_key]
            if parent is not None and attr is not None:
                val = parent.get(attr) if isinstance(parent, dict) else getattr(parent, attr, None)
                if isinstance(val, list):
                    return val

        val = self._get("source", None) or self._get("collection", None)
        if isinstance(val, list):
            return val
        return []

    def get_effective_index(self) -> int:
        """Calculates k = offset + index."""
        raw_offset = self._get("offset", self.offset)
        try:
            offset_val = int(raw_offset)
        except (ValueError, TypeError):
            offset_val = self.offset
        return offset_val + self.index

    def get_item(self) -> str:
        """
        Retrieves the item frame key from the collection at the effective index.
        Returns an empty string for vacant slots to suppress texture rendering.
        """
        collection = self._get_collection()
        k = self.get_effective_index()
        if 0 <= k < len(collection):
            item = collection[k]
            if isinstance(item, str):
                return item
            if hasattr(item, "id"):
                return getattr(item, "id")
            if hasattr(item, "name"):
                return getattr(item, "name")
            if isinstance(item, dict):
                return item.get("id", item.get("name", ""))
            return str(item)
        return ""

    def get_status(self) -> str:
        """Returns IDLE for populated slots, and DISABLED for vacant slots."""
        collection = self._get_collection()
        k = self.get_effective_index()
        if 0 <= k < len(collection):
            return Statuses.IDLE.value
        return Statuses.DISABLED.value

    def is_vacant(self) -> bool:
        """Evaluates whether the effective index falls outside the collection bounds."""
        collection = self._get_collection()
        k = self.get_effective_index()
        return k < 0 or k >= len(collection)

    def bind(self, **kwargs) -> Tuple[Callable[[], str]]:
        return (self.get_item,)