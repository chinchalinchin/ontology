"""
# Ontology: app.game.menus.layout

Package for Menu spatial layouts and traversal graph generation.
"""
# Standard Libraries
from typing import List, Dict, Tuple, Union
import logging

# Application Libraries
from app.assets.base import Asset
from app.config.enums import Layouts, Alignments
from app.models.config import MenuPane, MenuWidget


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
            root_asset = widgets[root_cfg.id]
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
        asset = widgets.get(cfg.id)
        if not asset: return

        # Add to rendering list in exact DFS topological order
        flattened.append(asset)

        # Base Case: Controls/Widgets have no children to layout
        if not isinstance(cfg, MenuPane):
            return

        # Recursive Step: Parent computes absolute positions for immediate children
        children_assets = [widgets[c.id] for c in cfg.children if c.id in widgets]
        
        if cfg.layout == Layouts.DOCK:
            self._layout_dock(asset, children_assets, cfg.alignment, cfg.gap)
        elif cfg.layout in (Layouts.STACK, Layouts.NEST):
            self._layout_stack(asset, children_assets, cfg.alignment, cfg.gap)
        elif cfg.layout == Layouts.TAB:
            self._layout_tab(asset, children_assets) # Just assigns parent's (x,y) to all children

        # Now that children have absolute physical coordinates, tell them to layout THEIR children
        for child_cfg in cfg.children:
            self._compute_recursive(child_cfg, widgets, flattened)

    def _build_graph(self, 
        buttons: List[Asset]
    ) -> Dict[str, Dict[str, str]]:
        """
        Uses an Axis-Aligned Bounding Box (AABB) spatial projection algorithm 
        to link traversable Button widgets based on absolute coordinates.
        """
        graph = {}
        for b1 in buttons:
            b1_id = b1.id
            graph[b1_id] = {}
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
                graph[b1_id]['south'] = closest.id
            if north_candidates:
                closest = max(north_candidates, key=lambda b: b.state.position.y)
                graph[b1_id]['north'] = closest.id
            if east_candidates:
                closest = min(east_candidates, key=lambda b: b.state.position.x)
                graph[b1_id]['east'] = closest.id
            if west_candidates:
                closest = max(west_candidates, key=lambda b: b.state.position.x)
                graph[b1_id]['west'] = closest.id

        return graph