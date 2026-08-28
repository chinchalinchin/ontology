"""
# Ontology: app.hooks.provider

Package for ingame Menu instantiation.
"""
import logging
import functools
from typing import Dict

from app.assets.base import Asset
from app.config.enums import AssetCategories, AssetInstances, Statuses
from app.hooks.factory import Factory
from app.models.properties import WidgetProperties
from app.models.state import (
    DisplayState, 
    PaneState, 
    MeterState, 
    TraversalState
)
from app.models.adapters import PydanticPosition as Position
from app.models.config import WidgetRecipe, MenuConfiguration, MenuPane, MenuWidget

from app.game.menus.core import Menu, Widget, Binding
from app.game.menus.controllers.scroll import ScrollController
from app.game.menus.controllers.display import DisplayController
from app.game.menus.layout import LayoutEngine

import libs.graphics.render as render
from libs.core.models import Dimensions

logger = logging.getLogger(__name__)

class Provider:
    recipes: WidgetRecipe
    properties: WidgetProperties

    def __init__(self, 
        recipes: WidgetRecipe, 
        properties: WidgetProperties
    ):
        self.recipes = recipes
        self.properties = properties

    def _resolve(self, 
        bind_path: str, context: dict):
        """
        Resolves a string path (e.g., 'context.sprite.state.meters.health') into a live memory reference.
        """
        if not bind_path:
            return None
            
        parts = bind_path.split('.')
        if parts[0] == 'context':
            parts = parts[1:]
        
        try:
            return functools.reduce(
                lambda obj, attr: obj.get(attr) if isinstance(obj, dict) else getattr(obj, attr),
                parts,
                context
            )
        except AttributeError:
            return None

    def unpack(self, menu_id: str, config: MenuConfiguration, context: dict, screensize: Dimensions) -> Menu:
        """
        Unpacks a MenuConfiguration into a live Menu object containing a flattened, sorted widget dictionary.
        """
        widgets = {}
        
        for pane_cfg in config.roots:
            self._unpack_pane(pane_cfg, context, widgets)
            
        layout = LayoutEngine(screensize)
        flattened_list, graph = layout.compute(config.roots, widgets)
        
        # Rebuild dictionary honoring flattened list's Painter's Algorithm ordering (Python 3.7+ preserves insertion order)
        ordered_widgets = {w.id: w for w in flattened_list}
        
        ctrl = None
        if config.controller == 'scroll':
            ctrl = ScrollController()
        elif config.controller == 'display':
            ctrl = DisplayController()
            
        # Default focus to the first traversible button if graph is present
        focus = next(iter(graph.keys())) if graph else ""
            
        return Menu(
            id=menu_id,
            focus=focus,
            graph=graph,
            context=context,
            widgets=ordered_widgets,
            controller=ctrl
        )

    def _unpack_pane(self, pane: MenuPane, context: dict, widgets: Dict[str, Asset]) -> None:
        props = self.properties.panes.get(pane.id)
        recipe = self.recipes.panes
        
        pane_asset = Asset(
            taxonomy        = Factory.taxonomy(
                id          = pane.id, 
                name        = pane.name, 
                category    = AssetCategories.WIDGETS, 
                instance    = AssetInstances.PANES
            ),
            properties      = props,
            state           = PaneState(
                position    = Position(x=0, y=0),
                layout      = pane.layout,
                alignment   = pane.alignment,
                gap         = pane.gap,
                margins     = (0, 0, 0, 0) # TODO
            ),
            frame            = Factory.frame(recipe.frame) if recipe \
                                else Factory.frame(None),
            animation       = Factory.animation(recipe.animation) if recipe \
                                else Factory.animation(None)
        )
        widgets[pane.id] = pane_asset

        for child in pane.children:
            child_asset = self._unpack_widget(child, context)
            widgets[child.id] = child_asset

    def _unpack_widget(self, cfg: MenuWidget, context: dict) -> Widget:
        props_dict = getattr(self.properties, cfg.instance, {})
        props = props_dict.get(cfg.id)
        recipe = getattr(self.recipes, cfg.instance, None)

        if cfg.instance == AssetInstances.PAGES:
            resolved = self._resolve(cfg.bind.state, context) if cfg.bind and cfg.bind.state else ""
            content = resolved if resolved else ""
            w = props.dimensions.w if props and props.dimensions else 0
            l = props.dimensions.l if props and props.dimensions else 0
            canvas_ptr = render.canvas(w, l)
            state = DisplayState(
                position=Position(x=0, y=0),
                content=content,
                pageindex=0,
                pagesize=1, # TODO: Create task ticket to calculate true pagesize based on TTF font metrics bounds
                canvas=canvas_ptr,
                dirty=True
            )
        elif cfg.instance == AssetInstances.METERS:
            resolved = self._resolve(cfg.bind.state, context) if cfg.bind and cfg.bind.state else None
            reading = resolved.current if resolved else 0
            unit = resolved.maximum if resolved else 1
            state = MeterState(
                position=Position(x=0, y=0),
                reading=reading,
                unit=unit
            )
        elif cfg.instance == AssetInstances.BUTTONS:
            state = TraversalState(
                position=Position(x=0, y=0),
                status=cfg.status or Statuses.IDLE,
                icons=[]
            )
        else:
            state = None

        binding = Binding(
            selection=cfg.bind.selection if cfg.bind else None,
            selector=cfg.bind.selector if cfg.bind else None,
            state=cfg.bind.state if cfg.bind else None
        )

        return Widget(
            taxonomy=Factory.taxonomy(cfg.id, cfg.name, AssetCategories.WIDGETS, cfg.instance),
            properties=props,
            state=state,
            frame=Factory.frame(recipe.frame) if recipe else Factory.frame(None),
            animation=Factory.animation(recipe.animation) if recipe else Factory.animation(None),
            binding=binding
        )