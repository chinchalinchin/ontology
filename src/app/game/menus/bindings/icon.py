"""
@domain.concrete
@domain.user
@app.menu
@menu.binding

# Ontology: Source - app.game.menus.bindings.icon

Icon Widget Binding implementation.
"""
# Standard Libraries
from typing import (
    Callable,
    Tuple
)

# Application Libraries
from app.models.config.menus import IconTarget
from app.models.menus.contexts import MenuContext
from app.game.menus.bindings.base import Binding

class IconBinding(Binding):
    target: IconTarget

    def __init__(self, target: IconTarget, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self._ref = self._resolve_path(target.icon, context)

    def get_icon(self) -> str:
        return self._deref(self._ref, "")

    def bind(self, **kwargs) -> Callable[[], str]:
        return self.get_icon