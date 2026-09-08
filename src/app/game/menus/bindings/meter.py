"""
# Ontology: app.game.menus.bindings.meter

Meter Widget Binding implementation.
"""
# Standard Libraries
from typing import Callable,Tuple

# Application Libraries
from app.game.menus.bindings.base import Binding

class MeterBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        def reading_function():
            target_state = self._get('meter')
            return getattr(target_state, 'current', target_state) if target_state is not None else 0
            
        def unit_function():
            target_state = self._get('meter')
            return getattr(target_state, 'maximum', 1) if target_state is not None else 1
            
        return (reading_function, unit_function)