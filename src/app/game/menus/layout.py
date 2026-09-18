"""
# Ontology: app.game.menus.layout

Package for Menu spatial layouts and traversal graph generation.
"""
# Standard Libraries
from typing import (
    List, 
    Dict, 
    Tuple, 
    Union,
    Any
)
import logging

# Application Libraries
from app.assets.base import Asset
from app.config.enums import (
    AssetInstances,
    Layouts, 
    Alignments, 
    Traversal, 
    Statuses
)
from app.models.config.menus import (
    MenuNode,
    PaneParameters
)

# Cython Libraries
from libs.core.models import Position, Dimensions

logger = logging.getLogger(__name__)


class Layout:
    screensize: Dimensions

    def __init__(self, screensize: Dimensions):
        self.screensize = screensize

    def compute(self, root_cfgs: List[MenuNode], widgets: Dict[str, Asset]) -> Tuple[List[Asset], Dict]:
        flattened = []
        
        for root_cfg in root_cfgs:
            root_asset = widgets.get(root_cfg.name)
            if not root_asset:
                continue

            pos = None
            if isinstance(root_cfg.parameters, PaneParameters):
                pos = root_cfg.parameters.position
            elif isinstance(root_cfg.parameters, dict):
                pos = root_cfg.parameters.get("position")

            if pos:
                root_asset.state.position = Position(
                    x=int(pos.px * self.screensize.w),
                    y=int(pos.py * self.screensize.l)
                )

            self._compute_recursive(root_cfg, widgets, flattened)

        graph = self._build_graph([w for w in flattened if w.instance == AssetInstances.BUTTONS.value])
        return flattened, graph

    def _compute_recursive(self, cfg: MenuNode, widgets: Dict[str, Asset], flattened: List[Asset]) -> None:
        asset = widgets.get(cfg.name)
        if not asset:
            return

        flattened.append(asset)

        # Non-pane endpoints terminate branch recursion
        if cfg.instance not in (AssetInstances.PANES.value, "panes"):
            return

        params = cfg.parameters
        if isinstance(params, PaneParameters):
            layout = params.layout
            alignment = params.alignment
            gap = params.gap
            children = params.children
        elif isinstance(params, dict):
            layout = params.get("layout", Layouts.STACK)
            alignment = params.get("alignment", Alignments.START)
            gap = params.get("gap", 0)
            children = params.get("children", [])
        else:
            return

        children_assets = [widgets[c.name] for c in children if c.name in widgets]
        
        if layout == Layouts.DOCK:
            self._layout_dock(asset, children_assets, alignment, gap)
        elif layout == Layouts.STACK:
            self._layout_stack(asset, children_assets, alignment, gap)
        elif layout == Layouts.OVERLAY:
            self._layout_overlay(asset, children_assets)

        for child_cfg in children:
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
        
        total_w = sum((c.dimensions.w if c.dimensions else 0) for c in children) + gap * (len(children) - 1)
        pane_w = (pane.dimensions.w - 2 * margin) if pane.dimensions else total_w
        
        if alignment == Alignments.CENTER:
            current_x += (pane_w - total_w) // 2
        elif alignment == Alignments.END:
            current_x += (pane_w - total_w)

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
        
        total_l = sum((c.dimensions.l if c.dimensions else 0) for c in children) + gap * (len(children) - 1)
        pane_l = (pane.dimensions.l - 2 * margin) if pane.dimensions else total_l

        if alignment == Alignments.CENTER:
            current_y += (pane_l - total_l) // 2
        elif alignment == Alignments.END:
            current_y += (pane_l - total_l)

        pane_w = (pane.dimensions.w - 2 * margin) if pane.dimensions else max((c.dimensions.w if c.dimensions else 0) for c in children)

        for child in children:
            w = child.dimensions.w if child.dimensions else 0
            l = child.dimensions.l if child.dimensions else 0
            x_offset = (pane_w - w) // 2
            
            child.state.position = Position(x=current_x + x_offset, y=current_y)
            current_y += l + gap

    def _layout_overlay(self, pane: Asset, children: List[Asset]):
        margin = getattr(pane.state, 'margins', 0)
        pane_x = pane.state.position.x + margin
        pane_y = pane.state.position.y + margin
        
        pane_w = (pane.dimensions.w - 2 * margin) if pane.dimensions else 0
        pane_l = (pane.dimensions.l - 2 * margin) if pane.dimensions else 0

        for child in children:
            child_w = child.dimensions.w if child.dimensions else 0
            child_l = child.dimensions.l if child.dimensions else 0
            
            x_offset = (pane_w - child_w) // 2
            y_offset = (pane_l - child_l) // 2
            
            child.state.position = Position(
                x=pane_x + x_offset, 
                y=pane_y + y_offset
            )

    def _build_graph(self, buttons: List[Asset]) -> Dict[str, Dict[str, str]]:
        graph = {}
        for b1 in buttons:
            if b1.state.status == Statuses.DISABLED.value:
                continue 

            b1_name = b1.name
            graph[b1_name] = {}
            b1_pos = b1.state.position
            b1_dim = b1.dimensions
            
            if not b1_pos or not b1_dim:
                continue

            south_candidates, north_candidates = [], []
            east_candidates, west_candidates = [], []

            for b2 in buttons:
                if b1 == b2 or b2.state.status == Statuses.DISABLED.value: 
                    continue
                    
                b2_pos = b2.state.position
                b2_dim = b2.dimensions
                if not b2_pos or not b2_dim:
                    continue

                x_overlap = not (b1_pos.x + b1_dim.w <= b2_pos.x or b2_pos.x + b2_dim.w <= b1_pos.x)
                y_overlap = not (b1_pos.y + b1_dim.l <= b2_pos.y or b2_pos.y + b2_dim.l <= b1_pos.y)

                if x_overlap:
                    if b2_pos.y > b1_pos.y: 
                        south_candidates.append(b2)
                    if b2_pos.y < b1_pos.y: 
                        north_candidates.append(b2)

                if y_overlap:
                    if b2_pos.x > b1_pos.x: 
                        east_candidates.append(b2)
                    if b2_pos.x < b1_pos.x: 
                        west_candidates.append(b2)

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