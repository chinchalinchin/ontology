"""
# Ontology: app.hooks.provider

Package for ingame Menu instantiation.
"""
# Standard Libraries
import logging
import functools
from typing import (
    Dict, 
    Any, 
    List
)

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetCategories, 
    AssetInstances, 
    Statuses
)
from app.hooks.factory import Factory
from app.models.properties import WidgetProperties
from app.models.state import (
    DisplayState, 
    PaneState, 
    MeterState, 
    TraversalState,
    AnimationState
)
from app.models.config import (
    WidgetRecipe, 
    MenuConfiguration, 
    MenuPane, 
    MenuWidget
)
from app.game.menus.core import (
    Menu, 
    Widget, 
    Binding
)
from app.game.menus.layout import LayoutEngine

# Cython Libraries
import libs.graphics.render as render
from libs.core.models import Dimensions, Position
from libs.graphics.registry import Registry

logger = logging.getLogger(__name__)

class Provider:
    recipes: WidgetRecipe
    properties: WidgetProperties

    def __init__(self, 
        recipes: WidgetRecipe, 
        properties: WidgetProperties,
        registry: Registry = None
    ):
        self.recipes = recipes
        self.properties = properties
        self.registry = registry

    def _paginate(self, text: str, font: Any, w: int, l: int) -> List[str]:
        """
        Calculates line-breaks and returns a list of perfectly fitted strings, 
        where each string represents a single page with explicit '\n' breaks.
        """
        if not text or not font:
            return [text]
            
        margin_w = int(w * font.margins)
        margin_l = int(l * font.margins)
        
        wrap_width = w - (2 * margin_w)
        wrap_height = l - (2 * margin_l)
        
        if wrap_width <= 0 or wrap_height <= 0:
            return [text]
            
        words = text.split(' ')
        lines = []
        current_line = ""
        
        # 1. Word wrap into distinct lines
        for word in words:
            test_line = f"{current_line} {word}".strip()
            tw, th = render.measure(test_line, font)
            
            if tw > wrap_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
            
        if not lines:
            return [""]
            
        # 2. Divide lines into pages based on vertical canvas constraints
        _, line_height = render.measure(lines[0], font)
        if line_height <= 0:
            line_height = 10 # Fallback failsafe
            
        max_lines_per_page = max(1, wrap_height // line_height)
        
        pages = []
        for i in range(0, len(lines), max_lines_per_page):
            page_lines = lines[i : i + max_lines_per_page]
            pages.append("\n".join(page_lines))
            
        return pages
    
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

    def _unpack_node(self, 
        cfg: Union[MenuPane, MenuWidget], 
        context: dict, 
        widgets: Dict[str, Asset]
    ) -> None:
        """
        Recursive router for unpacking the Menu Tree.
        """
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
        widgets[pane.name] = pane_asset
    
        # 2. Recurse into children
        for child in pane.children:
            self._unpack_node(child, context, widgets)

    def _unpack_widget(self, cfg: MenuWidget, context: dict) -> Widget:
        props_dict = getattr(self.properties, cfg.instance, {})
        props = props_dict.get(cfg.id)
        recipe = getattr(self.recipes, cfg.instance, None)

        if cfg.instance == AssetInstances.PAGES:
            resolved = self._resolve(cfg.bind.state, context) if cfg.bind and cfg.bind.state else ""
            content = resolved if resolved else ""
            w = props.dimensions.w
            l = props.dimensions.l
            canvas_ptr = render.canvas(w, l)
            is_text = isinstance(content, str)
            
            # Execute physical measurements only if we possess the text and the Font Registry
            if is_text and content:
                font = self.registry.font("dialogue") 
                content = self._paginate(content, font, w, l)
                
            state = DisplayState(
                position=Position(x=0, y=0),
                content=content,
                pageindex=0,
                pagesize=1, # One aggregated string page or one icon per page
                canvas=canvas_ptr,
                text=is_text
            )
        elif cfg.instance == AssetInstances.METERS:
            resolved = self._resolve(cfg.bind.state, context) if cfg.bind and cfg.bind.state else None
            # Inject dynamic getter closures to continuously evaluate the bound memory reference
            reading_function = lambda r=resolved: (
                r.current if hasattr(r, 'current') 
                    else (r if isinstance(r, (int, float)) else 0)
            )
            unit_function = lambda r=resolved: (
                r.maximum if hasattr(r, 'maximum') 
                    else (1 if isinstance(r, (int, float)) else 1)
            )
            state = MeterState(
                position=Position(x=0, y=0),
                reading_function = reading_function,
                unit_function = unit_function
            )
            if state.unit > 0:
                state.animation.frame = max(0, min(100, int(round((state.reading / state.unit) * 100))))

        elif cfg.instance == AssetInstances.BUTTONS:
            initial_status = cfg.status.value if cfg.status else Statuses.IDLE.value
            state = TraversalState(
                position=Position(x=0, y=0),
                status=cfg.status.value or Statuses.IDLE.value,
                icons=[],
                animation=AnimationState(action=initial_status) 
            )
        else:
            state = None

        binding = Binding(
            selection=cfg.bind.selection if cfg.bind else None,
            selector=cfg.bind.selector if cfg.bind else None,
            state=cfg.bind.state if cfg.bind else None
        )
        frame = Factory.frame(recipe.frame) \
                    if recipe else Factory.frame(None)
        animation = Factory.animation(recipe.animation) \
                        if recipe else Factory.animation(None)
        taxonomy = Factory.taxonomy(cfg.id, cfg.name, AssetCategories.WIDGETS, cfg.instance)

        logger.info(
            f"Unpacked Widget: {cfg.name} | "
            f"Recipe Frame: {recipe.frame} | "
            f"Resolved Frame: {type(frame).__name__}"
            f"Recipe Animation: {recipe.animation} | "
            f"Resolved Animation: {type(animation).__name__}"
        )

        return Widget(
            taxonomy=taxonomy,
            properties=props,
            state=state,
            frame=frame,
            animation=animation,
            binding=binding
        )

    def unpack(self, id: str, config: MenuConfiguration, context: dict, screensize: Dimensions) -> Menu:
        """
        Unpacks a MenuConfiguration into a live Menu object containing a flattened, sorted widget dictionary.
        """
        widgets = {}
        
        for pane in config.roots:
            self._unpack_pane(pane, context, widgets)
            
        layout = LayoutEngine(screensize)
        flattened_list, graph = layout.compute(config.roots, widgets)
        
        # Rebuild dictionary honoring flattened list's Painter's Algorithm ordering 
        #   (Python 3.7+ preserves insertion order)
        ordered_widgets = { w.name: w for w in flattened_list}
        
        ctrl = Factory.controller(config.controller)

        # Default focus to the first traversible button if graph is present
        focus = next(iter(graph.keys())) if graph else ""
            
        return Menu(
            id          = id,
            focus       = focus,
            graph       = graph,
            context     = context,
            widgets     = ordered_widgets,
            controller  = ctrl
        )