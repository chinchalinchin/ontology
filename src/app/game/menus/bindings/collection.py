"""
@domain.concrete
@domain.user
@app.menu
@menu.binding
@menu.gizmo

# Ontology: Source - app.game.menus.bindings.collection

Package for binding collection data to Gizmo slots.
"""
# Standard Libraries
from typing import (
    Callable, 
    Tuple, 
    Any, 
    List
)
import logging

# Application Libraries
from app.game.menus.bindings.base import Binding
from app.models.config.menus import CollectionTarget
from app.models.menus.contexts import MenuContext
from app.static.semantics import Statuses

logger = logging.getLogger(__name__)


class CollectionBinding(Binding):
    """
    ## CollectionBinding

    Binding component for collection elements (e.g., inventory slots, trade grids).
    Manages dynamic index slicing, pagination offsets, and bounds checking.
    """
    index: int
    offset: int

    def __init__(self, target: CollectionTarget, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self._source_ref = self._resolve_path(target.source, context)
        self.index = int(self.target.get("index", 0))
        self.offset = int(self.target.get("offset", 0))


    def get_collection(self) -> List[Any]:
        """Returns the evaluated collection list."""
        val = self._deref(self._source_ref)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return [k for k, qty in val.items() if qty > 0]
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
        collection = self.get_collection()
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
        collection = self.get_collection()
        k = self.get_effective_index()
        if 0 <= k < len(collection):
            return Statuses.IDLE.value
        return Statuses.DISABLED.value


    def is_vacant(self) -> bool:
        """Evaluates whether the effective index falls outside the collection bounds."""
        collection = self.get_collection()
        k = self.get_effective_index()
        return k < 0 or k >= len(collection)


    def bind(self, **kwargs) -> Callable[[], List[Any]]:
        return self.get_collection