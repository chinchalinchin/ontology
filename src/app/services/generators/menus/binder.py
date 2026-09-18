"""
# Ontology: app.services.generators.binder

Factory for generating and preparing Binding components.
"""
# Standard Libraries
from typing import Any, Optional, Dict

# Application Libraries
from app.config.enums import Bindings
from app.models.config.menus import MenuBinding
from app.game.menus.contexts import MenuContext
from app.game.menus.bindings import (
    Binding, 
    CollectionBinding,
    LibraryBinding, 
    MeterBinding, 
    IconBinding,
    SelectBinding, 
    TextBinding,
    ApertureBinding
)


class Binder:
    def __init__(self, registry: Any, library: Any):
        self.registry = registry
        self.library = library
        
    def binding(
        self, 
        bind: Optional[MenuBinding], 
        context: MenuContext, 
        widgets: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Binding]:
        if not bind:
            return None
            
        schema = bind.schema
        target = bind.target or {}
        
        resolved_kwargs = {
            'registry': self.registry,
            'library': self.library,
            'widgets': widgets or {},
            **kwargs
        }
        
        if schema == Bindings.LIBRARY.value:
            return LibraryBinding(target, context, **resolved_kwargs)
        elif schema == Bindings.METER.value:
            return MeterBinding(target, context, **resolved_kwargs)
        elif schema == Bindings.ICON.value:
            return IconBinding(target, context, **resolved_kwargs)
        elif schema == Bindings.SELECT.value:
            return SelectBinding(target, context, **resolved_kwargs)
        elif schema == Bindings.COLLECTION.value:
            return CollectionBinding(target, context, **resolved_kwargs)
        elif schema == Bindings.APERTURE.value:
            return ApertureBinding(target, context, **resolved_kwargs)
        else:
            return TextBinding(target, context, **resolved_kwargs)