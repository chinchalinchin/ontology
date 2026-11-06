"""
@domain.concrete
@domain.user
@app.menu
@menu.binding

# Ontology: Source - app.game.menus.bindings.select

Select Binding implementation.
"""
# Standard Libraries
from typing import Optional

# Application Libraries
from app.models.config.menus import SelectTarget
from app.game.menus.bindings.base import Binding

class SelectBinding(Binding):
    target: SelectTarget

    @property
    def selection(self) -> str:
        return self.target.selection

    @property
    def selector(self) -> Optional[str]:
        return self.target.selector

    @property
    def index(self) -> Optional[int]:
        return self.target.index

    def bind(self, **kwargs) -> None:
        return None