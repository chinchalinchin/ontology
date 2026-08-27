"""
# Ontology: app.hooks.provider

Package for ingame Menu instantiation.
"""

# Application Libraries
from app.assets.base import Asset
from app.assets.frames import DynamicFrame
from app.models.state import DisplayState
from app.models.adapters import (
    PydanticDimensions as Dimensions, 
    PydanticPosition as Position
)

# Cython Libraries
import libs.graphics.render as render

class Provider:
    pass


    def page(self, node_config, context):
        # ... resolve bindings and dimensions ...
        
        # TODO
        dimensions = Dimensions(w=10, l=1)
        resolved_text = "TODO"
        resolved_font = "TODO"

        # 1. Allocate a blank GPU canvas using Cython primitives
        text_canvas = render.canvas(w=dimensions.w, l=dimensions.l)
        
        # 2. Bake the text directly into the canvas
        font = self.registry.font(resolved_font)
        render.write(
            asset=(text_canvas, 0, 0, dimensions.w, dimensions.l, 0, 0, 0, 0),
            content=resolved_text, 
            font=font
        )
        
        # 3. Bind the pointer to the state
        state = DisplayState(..., canvas=text_canvas)
        
        return Asset(..., state=state, frame=DynamicFrame())