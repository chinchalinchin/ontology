"""
@domain.concrete
@domain.user
@app.menu
@menu.binding

# Ontology: Source - app.game.menus.bindings.select

Select Binding implementation.
"""
# Standard Libraries
from typing import Callable, Tuple

# Application Libraries
from app.game.menus.bindings.base import Binding

class SelectBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        return ()