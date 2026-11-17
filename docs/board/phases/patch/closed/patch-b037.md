#### Bug 037: Unculled Heap Allocations, Registry Lookups, and Full-Layer Sorting in `Screen._assemble`

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/app/game/screen.py` (`_assemble`, lines 126–205), the rendering pipeline executes operations in the following order every frame (60 Hz):

1. `self.board.renderables(player.state.layer)` (`src/app/game/engine.py`, line 127) returns the cached list of **all** non-tile assets on the active layer (`src/app/game/board/core.py`, line 276).
2. `assets.sort(key=self._sort)` (line 138) sorts the **entire layer's asset list** in-place ($O(N_{\text{layer}} \log N_{\text{layer}})$), mutating the list stored inside `Board._cache.cached_renderables[layer]`.
3. For **every** asset on the layer (lines 140–154), the loop calls `asset.frame.keys(asset.id, asset.state)`, `asset.frame.channels(...)`, and `self.registry.image(frame_key)` **before** checking whether the asset is inside the camera viewport (lines 171–174).

**Impact**:

In `StateFrame.keys` and `SpriteFrame.keys` (`src/app/assets/frames/sheets.py`, lines 46–51, 88–107), every call to `keys()` executes `settings.SEPARATOR.join([...])` and allocates a new list of tuples on the Python heap. If a layer contains $2,000$ assets and only $40$ are within the camera viewport (`pov`, `bounds`), the engine performs $2,000$ sort key evaluations, $2,000+$ dynamic string concatenations, list allocations, and `Registry.image()` dictionary lookups per frame ($120,000+$ allocations per second) only to discard $98\%$ of them at line 171.

**Remediation**:

Perform broad-phase camera AABB culling **first** using `asset.state.position` and `asset.dimensions` (with a constant margin $M$ for expression offsets), collect only the visible subset $V$ ($\vert{}V\vert{} \ll N_{\text{layer}}$), sort $V$ into a local list without mutating `Board._cache`, and invoke `asset.frame.keys()`, `asset.frame.channels()`, and `self.registry.image()` exclusively on $a \in V$:

$$\text{Complexity}_{\text{frame}}: \quad O(N_{\text{layer}} \log N_{\text{layer}}) + N_{\text{layer}} \cdot C_{\text{alloc}} \;\longrightarrow\; O(N_{\text{layer}}) + O(\vert{}V\vert{} \log \vert{}V\vert{}) + \vert{}V\vert{} \cdot C_{\text{alloc}}$$



```python
_CULL_MARGIN: int = 64

    def _in_viewport(
        self,
        asset: Asset,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> bool:
        """
        Broad-phase viewport AABB check. Bypasses unit-tile bounds for procedural
        multi-tile assets (Fluids, Shorelines) whose geometry extends beyond asset.dimensions.
        """
        if asset.instance in (
            AssetInstances.FLUIDS.value,
            AssetInstances.SHORELINES.value,
        ):
            return True

        px = asset.state.position.x
        py = asset.state.position.y
        dw = asset.dimensions.w if asset.dimensions else 0
        dl = asset.dimensions.l if asset.dimensions else 0

        return (
            px + dw >= min_x and px <= max_x and
            py + dl >= min_y and py <= max_y
        )

    def _assemble(
        self,
        assets: List[Asset],
        pov: Position,
        bounds: Dimensions,
    ) -> Tuple[list, list]:
        """
        Broad-phase culls assets to the camera viewport, height-sorts the visible
        subset, and assembles render primitives and auxiliary channel operations.
        """
        active_assets = []
        active_channels = []

        min_x = pov.x - self._CULL_MARGIN
        min_y = pov.y - self._CULL_MARGIN
        max_x = pov.x + bounds.w + self._CULL_MARGIN
        max_y = pov.y + bounds.l + self._CULL_MARGIN

        # 1. Broad-phase filter without mutating Board._cache.cached_renderables
        visible = [
            asset for asset in assets
            if asset.category != AssetCategories.TILES.value
            and self._in_viewport(asset, min_x, min_y, max_x, max_y)
        ]

        # 2. Height-sort only the visible subset prior to querying asset.frame.keys()
        visible.sort(key=self._sort)

        # 3. Narrow-phase frame resolution and crop culling
        for asset in visible:
            frame_keys = asset.frame.keys(asset.id, asset.state)
            channels = asset.frame.channels(asset.id, asset.state, asset.properties)
            submerge_channel = next(
                (
                    op for op in channels
                    if op[0] == ChannelTypes.SUBMERGE.value
                ),
                None,
            )

            for frame_key, ox, oy in frame_keys:
                tex_data = self.registry.image(frame_key)

                if not tex_data:
                    if not isinstance(asset.state, SheetState):
                        logger.warning(f"Registry MISS! Frame key not found: '{frame_key}'")
                    continue

                # Flatten mapping to C-level PRIMITIVE INTEGERS for destination logic
                tex, sx, sy, sw, sl = tex_data
                dx, dy = asset.state.position.x + ox, asset.state.position.y + oy
                dw, dl = sw, sl

                # Strict Culling: Only pass geometry if intersecting the target frame
                if (
                    dx + dw >= pov.x and dx <= pov.x + bounds.w and
                    dy + dl >= pov.y and dy <= pov.y + bounds.l
                ):
                    if submerge_channel is None:
                        active_assets.append((
                            tex, sx, sy, sw, sl,
                            dx, dy, dw, dl,
                            255, 255, 255, 255,
                        ))
                    else:
                        split_y, r, g, b, a = submerge_channel[1]
                        # Upper slice: normal rendering
                        active_assets.append((
                            tex, sx, sy, sw, split_y,
                            dx, dy, dw, split_y,
                            255, 255, 255, 255,
                        ))
                        # Lower slice: submerged texture modulation
                        rem_l = sl - split_y
                        active_assets.append((
                            tex, sx, sy + split_y, sw, rem_l,
                            dx, dy + split_y, dw, rem_l,
                            r, g, b, a,
                        ))

            # 4. Auxiliary Channel Tuples
            for c_type, payload in channels:
                if c_type == ChannelTypes.TINT.value:
                    cx, cy, cw, cl, r, g, b, a = payload
                    dx = asset.state.position.x + cx
                    dy = asset.state.position.y + cy
                    if (
                        dx + cw >= pov.x and dx <= pov.x + bounds.w and
                        dy + cl >= pov.y and dy <= pov.y + bounds.l
                    ):
                        active_channels.append((
                            c_type,
                            dx,
                            dy,
                            cw, cl,
                            r, g, b, a,
                        ))

        return active_assets, active_channels
```