"""
# Ontology: app.hooks.provider

Package for ingame Menu instantiation.
"""
# Standard Libraries
from typing import Any

# Application Libraries
from app.assets.base import Asset, Taxonomy
from app.config.enums import (
    AssetCategories,
    AssetInstances
)
from app.hooks.factory import Factory
from app.models.properties import WidgetProperties
from app.models.state import DisplayState
from app.models.adapters import PydanticPosition as Position
from app.models.config import RecipeConfiguration

# Cython Libraries
import libs.graphics.render as render

class Provider:

    def __init__(self, recipes: RecipeConfiguration):
        self.recipes = recipes

    def _resolve(self, bind_path: str, context: dict) -> Any:
        """
        """
        if not bind_path:
            return None
        parts = bind_path.split('.')
        if parts[0] == 'context':
            parts = parts[1:]
        
        obj = context
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                obj = getattr(obj, part, None)
        return obj


    def page(self, node, context, properties: WidgetProperties) -> Asset:
        """
        """
        resolved_lexicon = self._resolve(node.bind.state, context)
        # TODO: in future phase, retrieve library content from resolved_lexicon
        content = f"do something in future phase with: {resolved_lexicon}"
        blank_canvas = render.canvas(properties.dimensions.w, properties.dimensions.l)

        state = DisplayState(
            position=Position(x=0, y=0), # TODO: should be injected via Layout
            content=content,
            pageindex=0,
            pagesize=1, # TODO: ...calculate in __init__ of DisplayState? Not sure.
            canvas=blank_canvas,
            dirty=True
        )
        return Asset(
            properties = properties, 
            state = state, 
            taxonomy = Factory.taxonomy(node.id, node.name, AssetCategories.WIDGETS, AssetInstances.PAGES), 
            animation= Factory.animation(self.recipes.widgets.pages),
            frame= Factory.frame(self.recipes.widgets.pages)
        )