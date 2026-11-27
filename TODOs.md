```python


    @staticmethod
    def _subtract_rect(
        rect: Tuple[int, int, int, int],
        cutout: Tuple[int, int, int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Computes the exact disjoint 2D AABB difference rect \\ cutout, returning
        up to four residual (x1, y1, x2, y2) rectangles.
        """
        ax1, ay1, ax2, ay2 = rect
        bx1, by1, bx2, by2 = cutout

        if bx2 <= ax1 or bx1 >= ax2 or by2 <= ay1 or by1 >= ay2:
            return [rect]

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        residuals: List[Tuple[int, int, int, int]] = []
        if iy1 > ay1:
            residuals.append((ax1, ay1, ax2, iy1))
        if iy2 < ay2:
            residuals.append((ax1, iy2, ax2, ay2))
        if ix1 > ax1:
            residuals.append((ax1, iy1, ix1, iy2))
        if ix2 < ax2:
            residuals.append((ix2, iy1, ax2, iy2))
        return residuals


    @classmethod
    def _fluid_obstacles(
        cls,
        layer: str,
        board: Board,
        elevation: int,
        pad_x: float,
        pad_y: float
    ) -> List[Tuple[float, float, float, float]]:
        """
        Builds Minkowski-inflated obstacle AABBs for same-elevation Fluid
        corridors and pools, subtracting same-elevation Bridge footprints prior
        to inflation so river crossings remain navigable.
        """
        fluids = board.instances(AssetInstances.FLUIDS, layer, elevation=elevation)
        if not fluids:
            return []

        bridge_rects: List[Tuple[int, int, int, int]] = []
        for bridge in board.bridges(layer):
            if bridge.elevation != elevation:
                continue
            bx = int(bridge.state.position.x)
            by = int(bridge.state.position.y)
            hbs = bridge.hitbox.get(bridge.properties, bridge.state, elevation)
            if hbs:
                for hb in hbs:
                    bridge_rects.append((
                        bx + hb.position.x,
                        by + hb.position.y,
                        bx + hb.position.x + hb.dimensions.w,
                        by + hb.position.y + hb.dimensions.l,
                    ))
            else:
                bridge_rects.append((
                    bx,
                    by,
                    bx + bridge.dimensions.w,
                    by + bridge.dimensions.l,
                ))

        fluid_obstacles: List[Tuple[float, float, float, float]] = []
        for fluid in fluids:
            if not predicates.is_hazard(fluid):
                continue

            rects = predicates.fluid_rects(fluid)
            if not rects:
                continue

            for cutout in bridge_rects:
                next_rects: List[Tuple[int, int, int, int]] = []
                for rect in rects:
                    next_rects.extend(cls._subtract_rect(rect, cutout))
                rects = next_rects
                if not rects:
                    break

            for x1, y1, x2, y2 in rects:
                fluid_obstacles.append((
                    float(x1) - pad_x,
                    float(y1) - pad_y,
                    float(x2 - x1) + 2.0 * pad_x,
                    float(y2 - y1) + 2.0 * pad_y,
                ))

        return fluid_obstacles


    @classmethod
    def obstacles(
        cls,
        layer: str,
        board: Board,
        exclude: list,
        elevation: int = 0,
        pad_x: float = 0.0,
        pad_y: float = 0.0,
        fluid_pad_x: Optional[float] = None,
        fluid_pad_y: Optional[float] = None,
    ) -> list:
        """
        Transforms board weights, perimeters, and bridge-carved Fluid hazards
        for the specified elevation tier into flat C-primitive tuples,
        optionally inflated by Minkowski padding.
        """
        obstacles = []

        for asset in board.weights(layer, elevation=elevation):
            if asset.name in exclude:
                continue
            for hb in asset.hitbox.get(asset.properties, asset.state, elevation):
                obstacles.append((
                    float(asset.state.position.x + hb.position.x) - pad_x,
                    float(asset.state.position.y + hb.position.y) - pad_y,
                    float(hb.dimensions.w) + 2.0 * pad_x,
                    float(hb.dimensions.l) + 2.0 * pad_y,
                ))

        for bound in board.perimeters.get(layer, {}).get(elevation, []):
            obstacles.append((
                float(bound.position.x) - pad_x,
                float(bound.position.y) - pad_y,
                float(bound.dimensions.w) + 2.0 * pad_x,
                float(bound.dimensions.l) + 2.0 * pad_y,
            ))

        obstacles.extend(
            cls._fluid_obstacles(
                layer=layer,
                board=board,
                elevation=elevation,
                pad_x=pad_x if fluid_pad_x is None else fluid_pad_x,
                pad_y=pad_y if fluid_pad_y is None else fluid_pad_y,
            )
        )

        return obstacles
```