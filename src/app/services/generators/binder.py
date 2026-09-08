"""
# Ontology: app.services.generators.binder

Factory for generating and preparing Binding components.
"""
from typing import Any
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
        
        if schema == 'library':
            return LibraryBinding(target, context, **kwargs)
        elif schema == 'meter':
            return MeterBinding(target, context, **kwargs)
        elif schema == 'icon':
            return IconBinding(target, context, **kwargs)
        elif schema == 'select':
            return SelectBinding(target, context, **kwargs)
        else:
            return TextBinding(target, context, **kwargs)