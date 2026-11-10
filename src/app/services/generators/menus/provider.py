"""
@domain.system
@app.service
@app.menu
@app.asset
@category.widgets

# Ontology: Source - app.services.generators.menus.provider

Package for ingame Menu instantiation.
"""
from __future__ import annotations

# Standard Libraries
import logging
from typing import (
    Dict,
    Any,
    Optional,
    TYPE_CHECKING
)

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Statuses,
    Menus,
    Fonts,
    Shortcuts
)
from app.services.factories.assets import AssetFactory
from app.models.properties import WidgetProperties
from app.models.state import (
    PaneState,
    MeterState,
    TraversalState,
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
from app.models.menus import MenuContext
from app.game.menus.bindings import (
    Binding,
    CollectionBinding
)
from app.game.menus.modules import Layout
from app.services.generators.menus.fabricator import Fabricator

if TYPE_CHECKING:
    from app.services.generators.menus import Binder

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import (
    Dimensions,
    Position
)

logger = logging.getLogger(__name__)


class Provider:
    recipes: Any
    properties: WidgetProperties
    binder: Binder
    fabricator: Fabricator

    def __init__(
        self,
        recipes: Any,
        properties: WidgetProperties,
        binder: Binder,
        fabricator: Optional[Fabricator] = None
    ):
        self.recipes = recipes
        self.properties = properties
        self.binder = binder
        self.fabricator = fabricator or Fabricator()

    # --------------------------------------------------
    # ------------------------ ASSET HYDRATION UTILITIES
    # --------------------------------------------------

    def _meter(
        self,
        cfg: MenuNode,
        binding: Binding
    ) -> MeterState:
        reading_fn, unit_fn = binding.bind()
        return MeterState(
            id               = cfg.id,
            position         = Position(x=0, y=0),
            reading_function = reading_fn,
            unit_function    = unit_fn
        )

    def _icon(
        self,
        cfg: MenuNode,
        binding: Binding
    ) -> IconState:
        icon_function = binding.bind()
        return IconState(
            id            = cfg.id,
            position      = Position(x=0, y=0),
            icon_function = icon_function
        )

    def _button(
        self,
        cfg: MenuNode,
        binding: Optional[Binding]
    ) -> TraversalState:
        status_val = Statuses.IDLE.value
        if isinstance(cfg.parameters, ButtonParameters):
            status_val = cfg.parameters.status
        return TraversalState(
            id       = cfg.id,
            position = Position(x=0, y=0),
            status   = status_val
        )

    def _widget(
        self,
        cfg: MenuNode,
        context: MenuContext,
        widgets: Dict[str, Widget]
    ) -> Widget:
        props_dict = getattr(self.properties, cfg.instance, {})
        properties = props_dict.get(cfg.id)
        recipe = getattr(self.recipes, cfg.instance, None)
        instance_key = cfg.instance

        binding = self.binder.binding(cfg.bind, context, widgets=widgets)

        delegator = {
            AssetInstances.METERS.value: self._meter,
            AssetInstances.BUTTONS.value: self._button,
            AssetInstances.ICONS.value: self._icon
        }

        state = delegator[instance_key](cfg, binding)

        return AssetFactory.widget(cfg, properties, state, recipe, binding)

    def _bake_pane(self, widget: Widget) -> None:
        if not isinstance(widget.state, PaneState):
            return

        w = widget.dimensions.w
        l = widget.dimensions.l

        if widget.binding is not None and not isinstance(widget.binding, CollectionBinding):
            widget.state.content_function = widget.binding.bind(w=w, l=l)

        if w <= 0 or l <= 0:
            return

        canvas_ptr = render.canvas(w, l)
        widget.state.canvas = canvas_ptr

        primitives = []
        for key, ox, oy in widget.frame.keys(widget.id, widget.state):
            tex_data = self.binder.registry.image(key)
            if not tex_data:
                continue
            tex_ptr, sx, sy, sw, sl = tex_data
            primitives.append((tex_ptr, sx, sy, sw, sl, ox, oy, sw, sl, 1, 1))

        if primitives:
            render.construct(canvas_ptr, primitives)

        content = widget.state.current()
        if isinstance(content, str) and content:
            font = self.binder.registry.font(widget.state.font)
            if font:
                render.write((canvas_ptr, 0, 0, w, l, 0, 0, w, l), content, font)

    # --------------------------------------------------
    # ------------------------------ RECURSION UTILITIES
    # --------------------------------------------------

    def _unpack_node(
        self,
        cfg: MenuNode,
        context: MenuContext,
        widgets: Dict[str, Widget],
        font: Optional[Fonts]
    ) -> None:
        if cfg.instance == AssetInstances.PANES.value:
            self._unpack_pane(cfg, context, widgets, font)
        else:
            widgets[cfg.name] = self._widget(cfg, context, widgets)

    def _unpack_pane(
        self,
        pane: MenuNode,
        context: MenuContext,
        widgets: Dict[str, Widget],
        font: Optional[Fonts] = None
    ) -> None:
        """
        Hydrates a Pane node and recursively unpacks its children.
        """
        params = pane.parameters if isinstance(pane.parameters, PaneParameters) else PaneParameters()
        active_font = params.font or font or Fonts.DIALOGUE.value
        props = self.properties.panes.get(pane.id)
        recipe = self.recipes.panes

        binding = self.binder.binding(pane.bind, context, widgets=widgets, font=active_font)

        if isinstance(binding, CollectionBinding):
            state = CollectionState(
                id                  = pane.id,
                name                = pane.name,
                position            = Position(x=0, y=0),
                layout              = params.layout,
                alignment           = params.alignment,
                justification       = params.justification,
                gap                 = params.gap,
                margins             = params.margins,
                font                = active_font,
                collection_function = binding.bind(),
                capacity            = binding.target.capacity,
                columns             = binding.target.columns,
                offset              = 0
            )
        else:
            state = PaneState(
                id            = pane.id,
                name          = pane.name,
                position      = Position(x=0, y=0),
                layout        = params.layout,
                alignment     = params.alignment,
                justification = params.justification,
                gap           = params.gap,
                margins       = params.margins,
                font          = active_font
            )

        pane_widget = AssetFactory.widget(
            pane,
            props,
            state,
            recipe,
            binding
        )
        widgets[pane.name] = pane_widget

        for child in params.children:
            self._unpack_node(child, context, widgets, active_font)

        # Synchronize initial slot button statuses for CollectionState gizmos
        if isinstance(state, CollectionState):
            self._sync_collection_slots(pane.name, state, widgets)

    @staticmethod
    def _sync_collection_slots(
        pane_name: str,
        state: CollectionState,
        widgets: Dict[str, Widget]
    ) -> None:
        for i in range(state.capacity):
            slot_widget = widgets.get(f"{pane_name}-slot-{i}")
            if slot_widget and isinstance(slot_widget.state, TraversalState):
                status = Statuses.IDLE.value if state.is_occupied(i) else Statuses.DISABLED.value
                slot_widget.state.status = status

    def _expand(self, node: MenuNode, context: MenuContext) -> MenuNode:
        """
        Recursively compiles virtual macro nodes (gizmos) into concrete pane subtrees.
        """
        if node.instance == Shortcuts.GIZMOS.value:
            expanded = self.fabricator.expand(node, context)
            return self._expand(expanded, context)

        if node.instance == AssetInstances.PANES.value:
            params = node.parameters if isinstance(node.parameters, PaneParameters) else PaneParameters()
            new_children = [self._expand(child, context) for child in params.children]
            new_params = PaneParameters(
                layout        = params.layout,
                alignment     = params.alignment,
                justification = params.justification,
                gap           = params.gap,
                margins       = params.margins,
                dimensions    = params.dimensions,
                font          = params.font,
                children      = new_children
            )
            return MenuNode(
                id         = node.id,
                name       = node.name,
                instance   = node.instance,
                bind       = node.bind,
                parameters = new_params
            )

        return node

    # --------------------------------------------------
    # ----------------------------------- MENU UTILITIES
    # --------------------------------------------------

    def _focus(
        self,
        id: str,
        widgets: Dict[str, Widget],
        graph: dict
    ) -> Optional[str]:
        if id == Menus.VIEW.value or not graph:
            return None

        for focus in graph.keys():
            if widgets[focus].state.status != Statuses.DISABLED.value:
                widgets[focus].state.status = Statuses.ACTIVE.value
                return focus

        return None

    # --------------------------------------------------
    # --------------------------------- PUBLIC INTERFACE
    # --------------------------------------------------

    def unpack(
        self,
        id: str,
        config: MenuConfiguration,
        context: MenuContext,
        screensize: Dimensions
    ) -> Menu:
        widgets: Dict[str, Widget] = {}

        # Phase 1: Pure AST Macro Expansion Pass
        expanded_roots = [self._expand(root, context) for root in config.roots]

        # Phase 2: ECS Asset & Widget Hydration Pass
        for root in expanded_roots:
            self._unpack_pane(root, context, widgets)

        # Phase 3: Spatial Layout & Navigation Topology Graph
        layout = Layout(screensize)
        flattened_list, graph = layout.compute(expanded_roots, widgets)

        # Phase 4: Deferred Text Binding & 9-Slice Canvas Baking
        for widget in flattened_list:
            if isinstance(widget.state, PaneState):
                self._bake_pane(widget)

        ordered_widgets = {w.name: w for w in flattened_list}
        ctrl = AssetFactory.controller(config.controller)
        focus = self._focus(id, ordered_widgets, graph)

        return Menu(
            id         = id,
            focus      = focus,
            graph      = graph,
            context    = context,
            widgets    = ordered_widgets,
            controller = ctrl
        )