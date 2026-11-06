"""
@domain.concrete
@domain.user
@app.menu
@menu.binding
@menu.gizmo

# Ontology: Source - app.game.menus.bindings.aperture

Package for binding delegated aperture slot icons to parent Gizmo collection state.
"""
# Standard Libraries
from typing import (
    Callable, 
    Dict
)

# Application Libraries
from app.game.menus.core import Widget
from app.game.menus.bindings.base import Binding
from app.models.config.menus import ApertureTarget
from app.models.menus.contexts import MenuContext
from app.models.state.assets.widgets import CollectionState


class ApertureBinding(Binding):
    """
    ## ApertureBinding

    Delegates item frame key evaluation to a parent Gizmo pane's CollectionState.
    """
    target: ApertureTarget

    def __init__(self, 
        target: ApertureTarget, 
        context: MenuContext, 
        widgets: Dict[str, Widget] = None,
        **kwargs
    ):
        super().__init__(target, context, **kwargs)
        self.widgets = widgets if widgets is not None else {}

    def get_item(self) -> str:
        """
        Retrieves the current frame key from the parent Gizmo state.
        Returns an empty string if vacant or unresolvable to suppress rendering.
        """
        pane = self.widgets.get(self.target.selector)
        if pane is not None and isinstance(pane.state, CollectionState):
            return pane.state.get_item(self.target.index)
        return ""

    def bind(self, **kwargs) -> Callable[[], str]:
        return self.get_item
