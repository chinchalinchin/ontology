"""
# Ontology: app.services.generators.binder

Factory for generating and preparing Binding components.
"""
# Standard Libraries
from typing import Any

# Application Libraries
from app.config.enums import Bindings
from app.models.config import MenuBinding
from app.game.menus.contexts import MenuContext
from app.game.menus.bindings import (
    Binding, 
    LibraryBinding, 
    MeterBinding, 
    IconBinding,
    SelectBinding, 
    TextBinding
)

class Binder:
    def __init__(self, registry: Any, library: Any):
        self.registry = registry
        self.library = library
        
    def binding(self, bind: MenuBinding, context: MenuContext) -> Binding:
        if not bind:
            return None
            
        schema = bind.schema
        target = bind.target or {}
        
        kwargs = {
            'registry': self.registry,
            'library': self.library
        }
        
        if schema == Bindings.LIBRARY.value:
            return LibraryBinding(target, context, **kwargs)
        elif schema == Bindings.METER.value:
            return MeterBinding(target, context, **kwargs)
        elif schema == Bindings.ICON.value:
            return IconBinding(target, context, **kwargs)
        elif schema == Bindings.SELECT.value:
            return SelectBinding(target, context, **kwargs)
        else:
            return TextBinding(target, context, **kwargs)