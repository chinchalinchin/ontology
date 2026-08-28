"""
# Ontology: app.game.menus.layout

Package for Menu spatial layouts and traversal graph generation.
"""
# Standard Libraries
from typing import List, Dict, Tuple
import logging

# Application Libraries
from app.assets.base import Asset
from app.config.enums import Layouts, Alignments, AssetInstances
from app.models.config import MenuPane


# Cython Libraries
from libs.core.models import Position, Dimensions

logger = logging.getLogger(__name__)

class LayoutEngine:
    screensize: Dimensions

    def __init__(self, screensize: Dimensions):
        self.screensize = screensize

    def compute(self, 
        root_cfgs: List[MenuPane], 
        widgets: Dict[str, Asset]
    ) -> Tuple[List[Asset], Dict[str, Dict[str, str]]]:
        flattened = []

        for pane_cfg in root_cfgs:
            pane_asset = widgets.get(pane_cfg.id)
            if not pane_asset:
                continue

            # 1. Resolve Anchor
            sp = pane_cfg.position
            anchor_x = int(sp.px * self.screensize.w)
            anchor_y = int(sp.py * self.screensize.l)
            pane_asset.state.position = Position(x=anchor_x, y=anchor_y)

            # 2. Z-Sorting Base (Height and Depth)
            # Ensure the pane renders strictly above standard world assets
            pane_asset.state.height = 9999 
            pane_asset.state.depth = 10
            
            flattened.append(pane_asset)

            children = []
            for c_cfg in pane_cfg.children:
                child = widgets.get(c_cfg.id)
                if child:
                    children.append(child)

            # 3. Apply Spatial Algorithm
            if pane_cfg.layout == Layouts.DOCK:
                self._layout_dock(pane_asset, children, pane_cfg.alignment, pane_cfg.gap)
            elif pane_cfg.layout == Layouts.STACK:
                self._layout_stack(pane_asset, children, pane_cfg.alignment, pane_cfg.gap)
            else:
                # TODO: Create Task Board issue to implement TAB and NEST recursive rendering logic
                logger.warning(f"Layout algorithm '{pane_cfg.layout}' not fully implemented.")

            for c in children:
                # Ensure children render directly on top of the parent pane
                c.state.height = 9999
                c.state.depth = 11 
                flattened.append(c)

        # 4. Generate Traversal Graph
        buttons = [
            w for w in flattened 
            if w.instance == AssetInstances.BUTTONS and w.state.status.value != 'disabled'
        ]
        graph = self._build_graph(buttons)

        return flattened, graph

    def _layout_dock(self, 
        pane: Asset, 
        children: List[Asset], 
        alignment: Alignments, 
        gap: int
    ):
        current_x = pane.state.position.x
        current_y = pane.state.position.y
        
        # Simple Left (Start) alignment 
        # TODO: Adjust for Alignments.CENTER / Alignments.END based on Max Width offsets
        for child in children:
            child.state.position = Position(x=current_x, y=current_y)
            w = child.dimensions.w if child.dimensions else 0
            current_x += w + gap

    def _layout_stack(self,
        pane: Asset, 
        children: List[Asset], 
        alignment: Alignments,
        gap: int
    ):
        current_x = pane.state.position.x
        current_y = pane.state.position.y
        
        # Simple Top (Start) alignment
        for child in children:
            child.state.position = Position(x=current_x, y=current_y)
            l = child.dimensions.l if child.dimensions else 0
            current_y += l + gap

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