"""
@domain.system
@app.services
@workflow.menus

# Ontology: Source - app.services.generators.binder

Factory for generating and preparing Binding components.
"""
# Standard Libraries
from typing import Any, Optional, Dict

# Application Libraries
from app.static.semantics import Bindings
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

# ---------------------------------------------------

class Binder:
    _BINDING_MAP = {
        Bindings.LIBRARY.value: LibraryBinding,
        Bindings.METER.value: MeterBinding,
        Bindings.ICON.value: IconBinding,
        Bindings.SELECT.value: SelectBinding,
        Bindings.COLLECTION.value: CollectionBinding,
        Bindings.APERTURE.value: ApertureBinding,
        Bindings.TEXT.value: TextBinding
    }

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

        target_cls = self._BINDING_MAP.get(schema, TextBinding)
        return target_cls(target, context, **resolved_kwargs)