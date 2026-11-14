"""
@domain.concrete
@app.menu
@menu.binding
@menu.gizmo

# Ontology: Source - app.game.menus.bindings.collection

Package for binding collection data models to Gizmo panes.
"""
# Standard Libraries
from typing import (
    Callable,
    List
)

# Application Libraries
from app.game.menus.bindings.base import Binding
from app.models.config.menus import CollectionTarget
from app.models.menus import MenuContext


class CollectionBinding(Binding):
    """
    ## CollectionBinding

    Resolves a contextual collection path (Dict[str, int] or List[str])
    into a live closure returning active item keys for CollectionState.
    """
    target: CollectionTarget

    def __init__(self, target: CollectionTarget, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self._source_ref = self._resolve_path(target.source, context)

    def get_collection(self) -> List[str]:
        """Resolves the active item keys from a list or quantity-mapped dictionary."""
        val = self._deref(self._source_ref)
        if isinstance(val, dict):
            return [ str(k) for k, qty in val.items() if qty > 0 ]
        if isinstance(val, list):
            return [ str(item) for item in val ]
        return []

    def bind(self, **kwargs) -> Callable[[], List[str]]:
        return self.get_collection