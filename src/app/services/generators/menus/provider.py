"""
# Ontology: app.services.generators.provider

Package for ingame Menu instantiation.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    Dict, 
    Any, 
    Union, 
    List,
    Optional,
    TYPE_CHECKING
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    Statuses, 
    Menus,
    Fonts
)
from app.services.generators.game.factory import Factory
from app.models.properties import WidgetProperties
from app.models.state import (
    DisplayState, 
    PaneState, 
    MeterState, 
    TraversalState,
    AnimationState,
    IconState
)
from app.models.config import (
    MenuConfiguration, 
    MenuPane, 
    MenuWidget,
    MenuGizmo
)
from app.game.menus.core import (
    Menu, 
    Widget
)
from app.game.menus.contexts import MenuContext
from app.game.menus.bindings import Binding
from app.game.menus.layout import Layout

if TYPE_CHECKING:
    from app.services.generators.menus import (
        Binder,
        Fabricator
    )

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import Dimensions, Position

logger = logging.getLogger(__name__)

class Provider:
    """
    """
    recipes: Any
    properties: WidgetProperties
    binder: Binder
    fabricator: Fabricator

    def __init__(self, 
        recipes: Any, 
        properties: WidgetProperties, 
        binder: Binder,
        fabricator: Optional[Fabricator] = None
    ):
        self.recipes = recipes
        self.properties = properties
        self.binder = binder
        self.fabricator = fabricator or Fabricator()



    def _unpack_page(self, 
        cfg: MenuWidget, 
        binding: Binding,
        font: Fonts
    ) -> DisplayState:
        props_dict = getattr(self.properties, cfg.instance, {})
        props = props_dict.get(cfg.id)
        
        w = props.dimensions.w
        l = props.dimensions.l
        canvas_ptr = render.canvas(w, l)

        logger.info(cfg)

        if binding:
            content_function = next(iter(binding.bind(w=w, l=w)))
        else:
            content_function = lambda: []
            
        return DisplayState(
            id                  = cfg.id,
            position            = Position(x=0, y=0),
            content_function    = content_function,
            font                = font, 
            pageindex           = 0,
            pagesize            = 1,
            canvas              = canvas_ptr
        )

                    
    def _unpack_meter(self, 
        cfg: MenuWidget, 
        binding: Binding
    ) -> MeterState:
        reading_fn, unit_fn = binding.bind()
        state = MeterState(
            id                  = cfg.id,
            position            = Position(x=0, y=0),
            reading_function    = reading_fn,
            unit_function       = unit_fn
        )
        
        if state.unit > 0:
            state.animation.frame = max(0, min(100, int(round((state.reading / state.unit) * 100))))

        return state


    def _unpack_icon(self, 
        cfg: MenuWidget, 
        binding: Binding
    ) -> IconState:
        icon_function = next(iter(binding.bind()))
        return IconState(
            id                  = cfg.id,
            position            = Position(x=0, y=0),
            icon_function       = icon_function
        )


    def _unpack_button(self, 
        cfg: MenuWidget, 
        binding: Binding
    ) -> TraversalState:
        return TraversalState(
            id                  = cfg.id,
            position            = Position(x=0, y=0),
            status              = cfg.status,
            animation           = AnimationState(action=cfg.status)
        )

    
    def _unpack_widget(self, 
        cfg: MenuWidget, 
        context: MenuContext,
        font: Fonts
    ) -> Widget:
        props_dict = getattr(self.properties, cfg.instance, {})
        properties = props_dict.get(cfg.id)
        recipe = getattr(self.recipes, cfg.instance, None)
        instance_key = cfg.instance

        # Build the ECS component using the factory
        binding = self.binder.binding(cfg.bind, context)

        delegator = {
            AssetInstances.PAGES.value: lambda c, b: self._unpack_page(c, b, font),
            AssetInstances.METERS.value: self._unpack_meter,
            AssetInstances.BUTTONS.value: self._unpack_button,
            AssetInstances.ICONS.value: self._unpack_icon
        }

        # Inject Component into State unpacking
        state = delegator[instance_key](cfg, binding)

        frame = Factory.frame(recipe.frame)
        animation = Factory.animation(recipe.animation)
        taxonomy = Factory.taxonomy(
            cfg.id, 
            cfg.name, 
            AssetCategories.WIDGETS.value, 
            cfg.instance
        )

        return Widget(
            taxonomy            = taxonomy,
            properties          = properties,
            state               = state,
            frame               = frame,
            animation           = animation,
            binding             = binding
        )


    def _unpack_node(self, 
        cfg: Union[MenuPane, MenuWidget, MenuGizmo], 
        context: MenuContext, 
        widgets: Dict[str, Asset],
        font: Fonts
    ) -> Union[MenuPane, MenuWidget]:
        """
        """
        if isinstance(cfg, MenuGizmo):
            expanded = self.fabricator.expand(cfg, context, self.properties)            
            self._unpack_pane(expanded, context, widgets, font)
            return expanded
        elif isinstance(cfg, MenuPane):
            self._unpack_pane(cfg, context, widgets, font)
            return cfg
        else:
            widgets[cfg.name] = self._unpack_widget(cfg, context, font)
            return cfg
            
    def _unpack_pane(self, 
        pane: MenuPane, 
        context: MenuContext, 
        widgets: Dict[str, Asset],
        font: Union[Fonts, None] = None
    ) -> None:
        props = self.properties.panes.get(pane.id)
        recipe = self.recipes.panes
        font = pane.font or font

        pane_asset              = Asset(
            taxonomy            = Factory.taxonomy(
                id              = pane.id, 
                name            = pane.name, 
                category        = AssetCategories.WIDGETS.value, 
                instance        = AssetInstances.PANES.value
            ),
            properties          = props,
            state               = PaneState(
                position        = Position(x=0, y=0),
                layout          = pane.layout,
                alignment       = pane.alignment,
                gap             = pane.gap,
                margins         = pane.margins
            ),
            frame               = Factory.frame(recipe.frame),
            animation           = Factory.animation(recipe.animation)
        )
        widgets[pane.name] = pane_asset
    
        for i, child in enumerate(pane.children):
            node = self._unpack_node(child, context, widgets, font)
            if node is not child:
                pane.children[i] = node

    def _focus(self, 
        id: str, 
        widgets: List[Asset], 
        graph: dict
    ) -> str:
        """
        Compute the initial focused widget in the Menu.
        """
        if id == Menus.VIEW.value or not graph:
            return None
        
        focus_names = iter(graph.keys())
        focus = next(focus_names, None)

        while focus is not None:
            if widgets[focus].state.status != Statuses.DISABLED.value:
                widgets[focus].state.status = Statuses.ACTIVE.value
                widgets[focus].state.animation.action = Statuses.ACTIVE.value
                return focus
            focus = next(focus_names, None)

        return None
            
    def unpack(self, 
        id: str, 
        config: MenuConfiguration, 
        context: dict, 
        screensize: Dimensions
    ) -> Menu:
        context = context or {}
            
        widgets = {}
        for pane in config.roots:
            self._unpack_pane(pane, context, widgets)
            
        layout = Layout(screensize)
        flattened_list, graph = layout.compute(config.roots, widgets)
        
        ordered_widgets = { w.name: w for w in flattened_list }
        ctrl = Factory.controller(config.controller)

        focus = self._focus(id, ordered_widgets, graph)

        return Menu(
            id                  = id,
            focus               = focus,
            graph               = graph,
            context             = context,
            widgets             = ordered_widgets,
            controller          = ctrl
        )