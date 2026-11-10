"""
@domain.user
@domain.logic
@app.module
@app.menu

# Ontology: Source - app.game.menus.modules.layout

Menu spatial layouts and traversal graph generation.

## TODOs

1. This seems like a service, not a game module.
"""
# Standard Libraries
import math
from typing import (
    List,
    Dict,
    Tuple
)
import logging

# Application Libraries
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances,
    Layouts,
    Alignments,
    Traversal,
    Statuses
)
from app.models.config.menus import (
    AxisAlignment,
    MenuNode,
    PaneParameters
)

# Cython Libraries
from libs.core.models import (
    Position,
    Dimensions,
    Multiple
)

# --------------------------------------------

logger = logging.getLogger(__name__)

# --------------------------------------------

class Layout:
    screensize: Dimensions

    def __init__(self, screensize: Dimensions):
        self.screensize = screensize

    @staticmethod
    def _resolve_axis(
        origin: int,
        span: int,
        content: int,
        margin: int,
        mode: str
    ) -> int:
        if mode == Alignments.START.value:
            return origin + margin
        if mode == Alignments.END.value:
            return origin + span - content - margin
        return origin + (span - content) // 2

    def _quantize(self, cfg: MenuNode, widgets: Dict[str, Asset]) -> None:
        if cfg.instance != AssetInstances.PANES.value:
            return

        pane = widgets.get(cfg.name)
        if not pane:
            return

        params = cfg.parameters if isinstance(cfg.parameters, PaneParameters) else PaneParameters()

        wc = pane.properties.dimensions.w // 3
        lc = pane.properties.dimensions.l // 3

        w_req = int(params.dimensions.pw * self.screensize.w)
        l_req = int(params.dimensions.pl * self.screensize.l)

        nx = max(0, math.ceil((w_req - 2 * wc) / wc)) if wc > 0 else 0
        ny = max(0, math.ceil((l_req - 2 * lc) / lc)) if lc > 0 else 0

        pane.state.multiple = Multiple(nx=nx, ny=ny)
        pane.state.span = Dimensions(w=(nx + 2) * wc, l=(ny + 2) * lc)

        for child_cfg in params.children:
            self._quantize(child_cfg, widgets)

    def compute(self, root_cfgs: List[MenuNode], widgets: Dict[str, Asset]) -> Tuple[List[Asset], Dict]:
        flattened: List[Asset] = []

        for root_cfg in root_cfgs:
            self._quantize(root_cfg, widgets)

        for root_cfg in root_cfgs:
            root_asset = widgets.get(root_cfg.name)
            if not root_asset:
                continue

            just = root_asset.state.justification
            margin = root_asset.state.margins
            span = root_asset.dimensions

            root_x = self._resolve_axis(0, self.screensize.w, span.w, margin, just.horizontal)
            root_y = self._resolve_axis(0, self.screensize.l, span.l, margin, just.vertical)
            root_asset.state.position = Position(x=root_x, y=root_y)

            self._compute_recursive(root_cfg, widgets, flattened)

        graph = self._build_graph([
            w
            for w in flattened
            if w.instance == AssetInstances.BUTTONS.value
        ])
        return flattened, graph

    def _compute_recursive(self, cfg: MenuNode, widgets: Dict[str, Asset], flattened: List[Asset]) -> None:
        asset = widgets.get(cfg.name)
        if not asset:
            return

        flattened.append(asset)

        # Non-pane endpoints terminate branch recursion
        if cfg.instance != AssetInstances.PANES.value:
            return

        params = cfg.parameters if isinstance(cfg.parameters, PaneParameters) else PaneParameters()
        layout = asset.state.layout
        alignment = asset.state.alignment
        gap = asset.state.gap
        children = params.children

        children_assets = [widgets[c.name] for c in children if c.name in widgets]

        if layout == Layouts.DOCK.value:
            self._layout_dock(asset, children_assets, alignment, gap)
        elif layout == Layouts.STACK.value:
            self._layout_stack(asset, children_assets, alignment, gap)
        elif layout == Layouts.OVERLAY.value:
            self._layout_overlay(asset, children_assets, alignment)

        for child_cfg in children:
            self._compute_recursive(child_cfg, widgets, flattened)

    def _layout_dock(
        self,
        pane: Asset,
        children: List[Asset],
        alignment: AxisAlignment,
        gap: int
    ) -> None:
        if not children:
            return

        margin = pane.state.margins
        pane_x = pane.state.position.x
        pane_y = pane.state.position.y
        pane_w = pane.dimensions.w
        pane_l = pane.dimensions.l

        total_w = sum(c.dimensions.w for c in children) + gap * (len(children) - 1)
        current_x = self._resolve_axis(pane_x, pane_w, total_w, margin, alignment.horizontal)

        for child in children:
            w = child.dimensions.w
            l = child.dimensions.l
            child_y = self._resolve_axis(pane_y, pane_l, l, margin, alignment.vertical)

            child.state.position = Position(x=current_x, y=child_y)
            current_x += w + gap

    def _layout_stack(
        self,
        pane: Asset,
        children: List[Asset],
        alignment: AxisAlignment,
        gap: int
    ) -> None:
        if not children:
            return

        margin = pane.state.margins
        pane_x = pane.state.position.x
        pane_y = pane.state.position.y
        pane_w = pane.dimensions.w
        pane_l = pane.dimensions.l

        total_l = sum(c.dimensions.l for c in children) + gap * (len(children) - 1)
        current_y = self._resolve_axis(pane_y, pane_l, total_l, margin, alignment.vertical)

        for child in children:
            w = child.dimensions.w
            l = child.dimensions.l
            child_x = self._resolve_axis(pane_x, pane_w, w, margin, alignment.horizontal)

            child.state.position = Position(x=child_x, y=current_y)
            current_y += l + gap

    def _layout_overlay(
        self,
        pane: Asset,
        children: List[Asset],
        alignment: AxisAlignment
    ) -> None:
        if not children:
            return

        margin = pane.state.margins
        pane_x = pane.state.position.x
        pane_y = pane.state.position.y
        pane_w = pane.dimensions.w
        pane_l = pane.dimensions.l

        for child in children:
            child_w = child.dimensions.w
            child_l = child.dimensions.l

            child_x = self._resolve_axis(pane_x, pane_w, child_w, margin, alignment.horizontal)
            child_y = self._resolve_axis(pane_y, pane_l, child_l, margin, alignment.vertical)

            child.state.position = Position(x=child_x, y=child_y)

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

                x_overlap = not (
                    b1_pos.x + b1_dim.w <= b2_pos.x
                    or
                    b2_pos.x + b2_dim.w <= b1_pos.x
                )
                y_overlap = not (
                    b1_pos.y + b1_dim.l <= b2_pos.y
                    or
                    b2_pos.y + b2_dim.l <= b1_pos.y
                )

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
                graph[b1_name][Traversal.SOUTH.value] = closest.name
            if north_candidates:
                closest = max(north_candidates, key=lambda b: b.state.position.y)
                graph[b1_name][Traversal.NORTH.value] = closest.name
            if east_candidates:
                closest = min(east_candidates, key=lambda b: b.state.position.x)
                graph[b1_name][Traversal.EAST.value] = closest.name
            if west_candidates:
                closest = max(west_candidates, key=lambda b: b.state.position.x)
                graph[b1_name][Traversal.WEST.value] = closest.name

        return graph