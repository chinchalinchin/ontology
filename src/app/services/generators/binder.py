"""
# Ontology: app.services.generators.binder

Factory for generating and preparing Binding components.
"""
from typing import Any
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
        
    def binding(self, bind_cfg: Any, context: dict) -> Binding:
        """
        Parses YAML schema and instantiates the correct Binding interface.
        """
        if not bind_cfg:
            return None
            
        schema = getattr(bind_cfg, 'schema', getattr(bind_cfg, 'type', None))
        target = getattr(bind_cfg, 'target', getattr(bind_cfg, 'state', None))
        
        # Consolidate dependencies to pass via kwargs
        kwargs = {
            'selection': getattr(bind_cfg, 'selection', None),
            'selector': getattr(bind_cfg, 'selector', None),
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
            # Fallback for basic variable string interpolation
            return TextBinding(target, context, **kwargs)