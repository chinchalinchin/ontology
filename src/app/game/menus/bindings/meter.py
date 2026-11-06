"""
@domain.concrete
@domain.user
@app.menu
@menu.binding

# Ontology: Source - app.game.menus.bindings.meter

Package for binding Meter Widget States to live Meter data models.
"""
# Standard Libraries
from typing import (
    Callable,
    Tuple,
    Union
)

# Application Libraries
from app.game.menus.bindings.base import Binding
from app.models.config.menus import MeterTarget
from app.models.menus import MenuContext


class MeterBinding(Binding):
    """
    ## MeterBinding

    Binds a Meter widget's reading and unit closures to a context Meter attribute.
    """
    target: MeterTarget

    def __init__(self, target: MeterTarget, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self._meter_ref = self._resolve_path(target.meter, context)

    def get_reading(self) -> Union[int, float]:
        meter = self._deref(self._meter_ref)
        return meter.current if meter is not None else 0

    def get_unit(self) -> Union[int, float]:
        meter = self._deref(self._meter_ref)
        return meter.maximum if meter is not None else 0

    def bind(
        self,
        **kwargs
    ) -> Tuple[Callable[[], Union[int, float]], Callable[[], Union[int, float]]]:
        return (self.get_reading, self.get_unit)