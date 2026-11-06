"""
@domain.concrete
@domain.user
@app.menu
@menu.binding

# Ontology: Source - app.game.menus.bindings.meter

Meter Widget Binding implementation.
"""
# Standard Libraries
from typing import (
    Callable,
    Tuple
)

# Application Libraries
from app.game.menus.bindings.base import Binding
from app.models.config.menus import MeterTarget

class MeterBinding(Binding):
    meter: MeterTarget

    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        def reading_function():
            return self.target.meter.current
            
        def unit_function():
            return self.target.meter.maximum

        return (reading_function, unit_function)