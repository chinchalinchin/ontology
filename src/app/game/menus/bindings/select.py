"""
# Ontology: app.game.menus.bindings

Package for binding Widget states to game state.
"""
# Standard Libraries
from typing import Callable, Tuple

# Application Libraries
from app.game.menus.bindings.base import Binding

class SelectBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        return ()