"""
# Ontology: app.services.generators.provider

Package for ingame Menu instantiation.
"""
import logging
from typing import Dict, Any, Union

from app.assets.base import Asset
from app.config.enums import AssetCategories, AssetInstances, Statuses, Menus
from app.services.orchestration.factory import Factory
from app.models.properties import WidgetProperties
from app.models.state import (
    DisplayState, 
    PaneState, 
    MeterState, 
    TraversalState,
    AnimationState,
    IconState
)
from app.models.config import MenuConfiguration, MenuPane, MenuWidget
from app.game.menus.core import Menu, Widget
from app.game.menus.bindings import Binding
from app.game.menus.layout import Layout
from app.services.generators.binder import Binder

import libs.graphics.render as render
from libs.core.models import Dimensions, Position
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

class Provider:
    recipes: Any
    properties: WidgetProperties
    binder: Binder

    def __init__(self, 
        recipes: Any, 
        properties: WidgetProperties, 
        binder: Binder
    ):
        self.recipes = recipes
        self.properties = properties
        self.binder = binder


    def _unpack_page(self, cfg: MenuWidget, binding: Binding) -> DisplayState:
        props_dict = getattr(self.properties, cfg.instance, {})
        props = props_dict.get(cfg.id)
        
        w = props.dimensions.w
        l = props.dimensions.l
        canvas_ptr = render.canvas(w, l)

        if binding:
            callables = binding.bind(w=w, l=l)
            content_function = callables[0] if callables else lambda: []
        else:
            content_function = lambda: []

        return DisplayState(
            id=cfg.id,
            position=Position(x=0, y=0),
            content_function=content_function,
            pageindex=0,
            pagesize=1,
            canvas=canvas_ptr
        )

                    
    def _unpack_meter(self, cfg: MenuWidget, binding: Binding) -> MeterState:
        if binding:
            callables = binding.bind()
            reading_fn, unit_fn = callables if len(callables) >= 2 else (lambda: 0, lambda: 1)
        else:
            reading_fn, unit_fn = lambda: 0, lambda: 1
            
        state = MeterState(
            id = cfg.id,
            position=Position(x=0, y=0),
            reading_function=reading_fn,
            unit_function=unit_fn
        )
        
        if state.unit > 0:
            state.animation.frame = max(0, min(100, int(round((state.reading / state.unit) * 100))))

        return state


    def _unpack_icon(self, cfg: MenuWidget, binding: Binding) -> IconState:
        if binding:
            callables = binding.bind()
            icon_function = callables[0] if callables else lambda: ""
        else:
            icon_function = lambda: ""

        return IconState(
            id = cfg.id,
            position=Position(x=0, y=0),
            icon_function=icon_function
        )



    def _unpack_button(self, cfg: MenuWidget, binding: Binding) -> TraversalState:
        return TraversalState(
            id = cfg.id,
            position=Position(x=0, y=0),
            status=cfg.status,
            animation=AnimationState(action=cfg.status)
        )

    
    def _unpack_widget(self, cfg: MenuWidget, context: dict) -> Widget:
        props_dict = getattr(self.properties, cfg.instance, {})
        properties = props_dict.get(cfg.id)
        recipe = getattr(self.recipes, cfg.instance, None)
        instance_key = cfg.instance

        # Build the ECS component using the factory
        binding = self.binder.binding(cfg.bind, context)

        delegator = {
            AssetInstances.PAGES.value: self._unpack_page,
            AssetInstances.METERS.value: self._unpack_meter,
            AssetInstances.BUTTONS.value: self._unpack_button,
            AssetInstances.ICONS.value: self._unpack_icon
        }

        # Inject Component into State unpacking
        state = delegator[instance_key](cfg, binding)

        frame = Factory.frame(recipe.frame) \
                    if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                    if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(
            cfg.id, 
            cfg.name, 
            AssetCategories.WIDGETS.value, 
            cfg.instance
        )

        return Widget(
            taxonomy=taxonomy,
            properties=properties,
            state=state,
            frame=frame,
            animation=animation,
            binding=binding
        )

    def _unpack_node(self, cfg: Union[MenuPane, MenuWidget], context: dict, widgets: Dict[str, Asset]) -> None:
        if isinstance(cfg, MenuPane):
            self._unpack_pane(cfg, context, widgets)
        else:
            widgets[cfg.name] = self._unpack_widget(cfg, context)

            
    def _unpack_pane(self, pane: MenuPane, context: dict, widgets: Dict[str, Asset]) -> None:
        props = self.properties.panes.get(pane.id)
        recipe = self.recipes.panes
        
        pane_asset = Asset(
            taxonomy        = Factory.taxonomy(
                id          = pane.id, 
                name        = pane.name, 
                category    = AssetCategories.WIDGETS.value, 
                instance    = AssetInstances.PANES.value
            ),
            properties      = props,
            state           = PaneState(
                position    = Position(x=0, y=0),
                layout      = pane.layout,
                alignment   = pane.alignment,
                gap         = pane.gap,
                margins     = pane.margins
            ),
            frame           = Factory.frame(recipe.frame) if recipe else Factory.frame(None),
            animation       = Factory.animation(recipe.animation) if recipe else Factory.animation(None)
        )
        widgets[pane.name] = pane_asset
    
        for child in pane.children:
            self._unpack_node(child, context, widgets)


    def unpack(self, id: str, config: MenuConfiguration, context: dict, screensize: Dimensions) -> Menu:
        context = context or {}
            
        widgets = {}
        for pane in config.roots:
            self._unpack_pane(pane, context, widgets)
            
        layout = Layout(screensize)
        flattened_list, graph = layout.compute(config.roots, widgets)
        
        ordered_widgets = { w.name: w for w in flattened_list }
        ctrl = Factory.controller(config.controller)

        focus = next(iter(graph.keys())) if graph and id != Menus.VIEW.value else ""

        if focus and focus in ordered_widgets:
            ordered_widgets[focus].state.status = Statuses.ACTIVE.value
            ordered_widgets[focus].state.animation.action = Statuses.ACTIVE.value

        return Menu(
            id          = id,
            focus       = focus,
            graph       = graph,
            context     = context,
            widgets     = ordered_widgets,
            controller  = ctrl
        )