"""
# Ontology: app.game.menus.bindings.icon

Icon Widget Binding implementation.
"""
# Standard Libraries
from typing import Callable,Tuple

# Application Libraries
import app.config.settings as settings
from app.game.menus.bindings.base import Binding

class IconBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        def icon_function():
            return self._get('icon', "")
        return (icon_function,)