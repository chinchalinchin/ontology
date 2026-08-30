"""
# Ontology: app.game.menus.layout

Package for Menu spatial layouts and traversal graph generation.
"""
# Standard Libraries
from typing import (
    List, 
    Dict, 
    Tuple, 
    Union
)
import logging

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    Layouts, 
    Alignments,
    Traversal
)
from app.models.config import (
    MenuPane, 
    MenuWidget
)

# Cython Libraries
from libs.core.models import Position, Dimensions

logger = logging.getLogger(__name__)

class LayoutEngine:
    screensize: Dimensions

    def __init__(self, screensize: Dimensions):
        self.screensize = screensize

    def compute(self, root_cfgs: List[MenuPane], widgets: Dict[str, Asset]) -> Tuple[List[Asset], Dict]:
        flattened = []
        
        for root_cfg in root_cfgs:
            # 1. Calculate the initial Root Anchor from percentages
            root_asset = widgets[root_cfg.name]
            if root_cfg.position:
                root_asset.state.position = Position(
                    x=int(root_cfg.position.px * self.screensize.w),
                    y=int(root_cfg.position.py * self.screensize.l)
                )
            # 2. Kick off the recursion
            self._compute_recursive(root_cfg, widgets, flattened)

        graph = self._build_graph([w for w in flattened if w.instance == 'buttons'])
        return flattened, graph

    def _compute_recursive(self, cfg: Union[MenuPane, MenuWidget], widgets: Dict, flattened: List) -> None:
        asset = widgets.get(cfg.name)
        if not asset: return

        # Add to rendering list in exact DFS topological order
        flattened.append(asset)

        # Base Case: Controls/Widgets have no children to layout
        if not isinstance(cfg, MenuPane):
            return

        # Recursive Step: Parent computes absolute positions for immediate children
        children_assets = [widgets[c.name] for c in cfg.children if c.name in widgets]
        
        if cfg.layout in (Layouts.DOCK, Layouts.ROW):
            self._layout_dock(asset, children_assets, cfg.alignment, cfg.gap)
        elif cfg.layout in (Layouts.STACK, Layouts.COLUMN):
            self._layout_stack(asset, children_assets, cfg.alignment, cfg.gap)
        elif cfg.layout == Layouts.TAB:
            self._layout_tab(asset, children_assets)

        # Now that children have absolute physical coordinates, tell them to layout THEIR children
        for child_cfg in cfg.children:
            self._compute_recursive(child_cfg, widgets, flattened)

    def _layout_dock(self, 
        pane: Asset, 
        children: List[Asset], 
        alignment: Alignments, 
        gap: int
    ):
        if not children:
            return

        margin = getattr(pane.state, 'margins', 0)
        current_x = pane.state.position.x + margin
        current_y = pane.state.position.y + margin
        
        # Main-axis (X) alignment calculation
        total_w = sum((c.dimensions.w if c.dimensions else 0) for c in children) + gap * (len(children) - 1)
        
        # Usable width subtracts both left and right margins
        pane_w = (pane.dimensions.w - 2 * margin) if pane.dimensions else total_w
        
        if alignment == Alignments.CENTER:
            current_x += (pane_w - total_w) // 2
        elif alignment == Alignments.END:
            current_x += (pane_w - total_w)

        # Cross-axis (Y) alignment: Center vertically within the usable Pane space
        pane_h = (pane.dimensions.l - 2 * margin) if pane.dimensions else max((c.dimensions.l if c.dimensions else 0) for c in children)

        for child in children:
            w = child.dimensions.w if child.dimensions else 0
            h = child.dimensions.l if child.dimensions else 0
            
            y_offset = (pane_h - h) // 2
            
            child.state.position = Position(x=current_x, y=current_y + y_offset)
            current_x += w + gap

    def _layout_stack(self,
        pane: Asset, 
        children: List[Asset], 
        alignment: Alignments,
        gap: int
    ):
        if not children:
            return

        margin = getattr(pane.state, 'margins', 0)
        current_x = pane.state.position.x + margin
        current_y = pane.state.position.y + margin
        
        # Main-axis (Y) alignment calculation
        total_l = sum((c.dimensions.l if c.dimensions else 0) for c in children) + gap * (len(children) - 1)
        
        # Usable length (height) subtracts top and bottom margins
        pane_l = (pane.dimensions.l - 2 * margin) if pane.dimensions else total_l

        if alignment == Alignments.CENTER:
            current_y += (pane_l - total_l) // 2
        elif alignment == Alignments.END:
            current_y += (pane_l - total_l)

        # Cross-axis (X) alignment: Center horizontally within the usable Pane space
        pane_w = (pane.dimensions.w - 2 * margin) if pane.dimensions else max((c.dimensions.w if c.dimensions else 0) for c in children)

        for child in children:
            w = child.dimensions.w if child.dimensions else 0
            l = child.dimensions.l if child.dimensions else 0
            
            x_offset = (pane_w - w) // 2
            
            child.state.position = Position(x=current_x + x_offset, y=current_y)
            current_y += l + gap

    def _layout_tab(self,
        pane: Asset,
        children: List[Asset]
    ):
        """
        Tabs superimpose children natively at the exact same anchor as the parent, offset by the margin.
        """
        margin = getattr(pane.state, 'margins', 0)
        for child in children:
            child.state.position = Position(
                x=pane.state.position.x + margin, 
                y=pane.state.position.y + margin
            )

    def _build_graph(self, 
        buttons: List[Asset]
    ) -> Dict[str, Dict[str, str]]:
        """
        Uses an Axis-Aligned Bounding Box (AABB) spatial projection algorithm 
        to link traversable Button widgets based on absolute coordinates.
        """
        graph = {}
        for b1 in buttons:
            b1_name = b1.name
            graph[b1_name] = {}
            b1_pos = b1.state.position
            b1_dim = b1.dimensions
            
            if not b1_pos or not b1_dim:
                continue

            south_candidates, north_candidates = [], []
            east_candidates, west_candidates = [], []

            for b2 in buttons:
                if b1 == b2: 
                    continue
                    
                b2_pos = b2.state.position
                b2_dim = b2.dimensions
                if not b2_pos or not b2_dim:
                    continue

                x_overlap = not (b1_pos.x + b1_dim.w <= b2_pos.x or b2_pos.x + b2_dim.w <= b1_pos.x)
                y_overlap = not (b1_pos.y + b1_dim.l <= b2_pos.y or b2_pos.y + b2_dim.l <= b1_pos.y)

                if x_overlap:
                    if b2_pos.y > b1_pos.y: south_candidates.append(b2)
                    if b2_pos.y < b1_pos.y: north_candidates.append(b2)

                if y_overlap:
                    if b2_pos.x > b1_pos.x: east_candidates.append(b2)
                    if b2_pos.x < b1_pos.x: west_candidates.append(b2)

            # Assign adjacent boundaries based on min/max distances
            if south_candidates:
                closest = min(south_candidates, key=lambda b: b.state.position.y)
                graph[b1_name][Traversal.SOUTH] = closest.name
            if north_candidates:
                closest = max(north_candidates, key=lambda b: b.state.position.y)
                graph[b1_name][Traversal.NORTH] = closest.name
            if east_candidates:
                closest = min(east_candidates, key=lambda b: b.state.position.x)
                graph[b1_name][Traversal.EAST] = closest.name
            if west_candidates:
                closest = max(west_candidates, key=lambda b: b.state.position.x)
                graph[b1_name][Traversal.WEST] = closest.name

        return graph