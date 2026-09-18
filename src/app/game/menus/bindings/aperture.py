"""
# Ontology: app.game.menus.bindings.aperture

Package for binding delegated aperture slot icons to parent Gizmo collection state.
"""
from typing import Tuple, Callable, Dict, Any
from app.game.menus.bindings.base import Binding
from app.game.menus.contexts import MenuContext


class ApertureBinding(Binding):
    """
    ## ApertureBinding

    Delegates item frame key evaluation to a parent Gizmo pane's CollectionState.
    """
    index: int
    widgets: Dict[str, Any]

    def __init__(self, target: dict, context: MenuContext, widgets: Dict[str, Any] = None, **kwargs):
        super().__init__(target, context, **kwargs)
        self.widgets = widgets or {}
        self.index = int(self.target.get("index", 0))


    def get_item(self) -> str:
        """
        Retrieves the current frame key from the parent Gizmo state.
        Returns an empty string if vacant or unresolvable to suppress rendering.
        """
        selector = self.target.get("selector")
        if selector and selector in self.widgets:
            target_pane = self.widgets[selector]
            if hasattr(target_pane.state, "get_item"):
                return target_pane.state.get_item(self.index)
        return ""


    def bind(self, **kwargs) -> Tuple[Callable[[], str]]:
        return (self.get_item,)