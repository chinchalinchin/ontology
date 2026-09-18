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
    Fonts,
    Bindings,
    Shortcuts
)
from app.services.generators.game.factory import Factory
from app.models.properties import WidgetProperties
from app.models.state import (
    DisplayState, 
    PaneState, 
    MeterState, 
    TraversalState, 
    AnimationState, 
    IconState,
    CollectionState
)
from app.models.config.menus import (
    MenuConfiguration, 
    MenuNode,
    PaneParameters,
    ButtonParameters
)
from app.game.menus.core import (
    Menu, 
    Widget
)
from app.game.menus.contexts import MenuContext
from app.game.menus.bindings import Binding
from app.game.menus.layout import Layout
from app.services.generators.menus.fabricator import Fabricator

if TYPE_CHECKING:
    from app.services.generators.menus import Binder
    

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import Dimensions, Position

logger = logging.getLogger(__name__)


class Provider:
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
        cfg: MenuNode, 
        binding: Binding, 
        font: Fonts
    ) -> DisplayState:
        props_dict = getattr(self.properties, cfg.instance, {})
        props = props_dict.get(cfg.id)
        
        w = props.dimensions.w
        l = props.dimensions.l
        canvas_ptr = render.canvas(w, l)

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
        cfg: MenuNode, 
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
        cfg: MenuNode, 
        binding: Binding
    ) -> IconState:
        icon_function = next(iter(binding.bind()))
        return IconState(
            id                  = cfg.id,
            position            = Position(x=0, y=0),
            icon_function       = icon_function
        )

    def _unpack_button(self, 
        cfg: MenuNode, 
        binding: Binding
    ) -> TraversalState:
        status_val = Statuses.IDLE.value
        if isinstance(cfg.parameters, ButtonParameters):
            status_val =  cfg.parameters.status
        return TraversalState(
            id                  = cfg.id,
            position            = Position(x=0, y=0),
            status              = status_val,
            animation           = AnimationState(action=status_val)
        )

    def _unpack_widget(self, 
        cfg: MenuNode, 
        context: MenuContext, 
        font: Fonts,
        widgets: Dict[str, Asset]
    ) -> Widget:
        props_dict = getattr(self.properties, cfg.instance, {})
        properties = props_dict.get(cfg.id)
        recipe = getattr(self.recipes, cfg.instance, None)
        instance_key = cfg.instance

        binding = self.binder.binding(cfg.bind, context, widgets=widgets)

        delegator = {
            AssetInstances.PAGES.value: lambda c, b: self._unpack_page(c, b, font),
            AssetInstances.METERS.value: self._unpack_meter,
            AssetInstances.BUTTONS.value: self._unpack_button,
            AssetInstances.ICONS.value: self._unpack_icon
        }

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
        cfg: MenuNode, 
        context: MenuContext, 
        widgets: Dict[str, Asset], 
        font: Fonts
    ) -> None:
        if cfg.instance == AssetInstances.PANES.value:
            self._unpack_pane(cfg, context, widgets, font)
        else:
            widgets[cfg.name] = self._unpack_widget(cfg, context, font, widgets)

    def _unpack_pane(self, 
        pane: MenuNode, 
        context: MenuContext, 
        widgets: Dict[str, Asset], 
        font: Union[Fonts, None] = None
    ) -> None:
        """
        """
        params = pane.parameters

        if not isinstance(params, PaneParameters):
            logger.warning(f"Pane does not have PaneParameters: {pane.name}")
            return 
        
        layout = params.layout
        alignment = params.alignment
        gap = params.gap
        margins = params.margins
        dimensions = params.dimensions
        font = params.font or font
        children = params.children

        props = self.properties.panes.get(pane.id)
        recipe = self.recipes.panes

        # Override dimensions on properties if declared on pane parameters
        if dimensions is not None:
            props = WidgetProperties(
                dimensions=dimensions,
                frames=props.frames
            )

        # Unpack collection pane state
        if pane.bind and pane.bind.schema == Bindings.COLLECTION.value:
            binding = self.binder.binding(pane.bind, context, widgets=widgets)
            collection_fn = next(iter(binding.bind()))
            target_dict = pane.bind.target
            capacity = int(target_dict.get("capacity", 8))
            columns = int(target_dict.get("columns", 4))

            state = CollectionState(
                position=Position(x=0, y=0),
                layout=layout,
                alignment=alignment,
                gap=gap,
                margins=margins,
                collection_function=collection_fn,
                capacity=capacity,
                columns=columns,
                offset=0
            )

            pane_asset = Widget(
                taxonomy=Factory.taxonomy(
                    id=pane.id,
                    name=pane.name,
                    category=AssetCategories.WIDGETS.value,
                    instance=AssetInstances.PANES.value
                ),
                properties=props,
                state=state,
                frame=Factory.frame(recipe.frame),
                animation=Factory.animation(recipe.animation),
                binding=binding
            )
        else:
            state = PaneState(
                position=Position(x=0, y=0),
                layout=layout,
                alignment=alignment,
                gap=gap,
                margins=margins
            )

            pane_asset = Asset(
                taxonomy=Factory.taxonomy(
                    id=pane.id,
                    name=pane.name,
                    category=AssetCategories.WIDGETS.value,
                    instance=AssetInstances.PANES.value
                ),
                properties=props,
                state=state,
                frame=Factory.frame(recipe.frame),
                animation=Factory.animation(recipe.animation)
            )

        widgets[pane.name] = pane_asset

        for child in children:
            self._unpack_node(child, context, widgets, font)


    def _focus(self, 
        id: str, 
        widgets: Dict[str, Asset], 
        graph: dict
    ) -> Optional[str]:
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


    def _expand_tree(self, node: MenuNode, context: MenuContext) -> MenuNode:
        """
        Recursively compiles virtual macro nodes (gizmos) into concrete pane subtrees.
        """
        if node.instance == Shortcuts.GIZMOS.value:
            expanded = self.fabricator.expand(node, context, self.properties)
            return self._expand_tree(expanded, context)

        if node.instance == AssetInstances.PANES.value:
            params = node.parameters
            if not isinstance(params, PaneParameters):
                logger.warning(f"Pane Node does not have Pane Parameters: {node.name}")
                return
            
            new_children = [self._expand_tree(child, context) for child in params.children]
            new_params = PaneParameters(
                layout=params.layout,
                alignment=params.alignment,
                gap=params.gap,
                margins=params.margins,
                position=params.position,
                dimensions=params.dimensions,
                font=params.font,
                children=new_children
            )
            return MenuNode(
                id=node.id,
                name=node.name,
                instance=node.instance,
                bind=node.bind,
                parameters=new_params
            )

        return node

    def unpack(self, 
        id: str, 
        config: MenuConfiguration, 
        context: dict, 
        screensize: Dimensions
    ) -> Menu:
        context = context or {}
        widgets = {}

        # Phase 1: Pure AST Macro Expansion Pass
        expanded_roots = [self._expand_tree(root, context) for root in config.roots]

        # Phase 2: ECS Asset & Widget Hydration Pass
        for root in expanded_roots:
            self._unpack_pane(root, context, widgets)

        # Phase 3: Spatial Layout & Navigation Topology Graph
        layout = Layout(screensize)
        flattened_list, graph = layout.compute(expanded_roots, widgets)

        ordered_widgets = {w.name: w for w in flattened_list}
        ctrl = Factory.controller(config.controller)
        focus = self._focus(id, ordered_widgets, graph)

        return Menu(
            id          = id,
            focus       = focus,
            graph       = graph,
            context     = context,
            widgets     = ordered_widgets,
            controller  = ctrl
        )