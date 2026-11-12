The primary architectural bottleneck in the current design is that `Screen` allocates monolithic textures (`bg_canvas` and `fg_canvas`) sized to the entire board:

```python
canvas_w = max(boardsize.w, screensize.w)
canvas_l = max(boardsize.l, screensize.l)
self.bg_canvas = render.canvas(canvas_w, canvas_l, opaque=is_opaque)
self.fg_canvas = render.canvas(canvas_w, canvas_l)

```

At $3000 \times 3000$ pixels, two 32-bit RGBA canvases consume:

$$\text{Memory} = 3000 \times 3000 \times 4 \times 2 \approx 72\text{ MB VRAM}$$

As dimensions scale to $8000 \times 8000$ or higher, this exceeds 500 MB of VRAM just for background/foreground passes, risks exceeding GPU hardware render-target limits (`max_texture_width`/`max_texture_height`), and stalls execution during level loading or season re-baking (`reconstruct`).

The optimal solution is **Fixed-Size Spatial Texture Chunking**, which retains the performance of pre-rendered static tiles (`render.construct`) while decoupling memory allocations from board size.

---

### 1. Architectural Strategy: Uniform Spatial Chunk Grid

Instead of two monolithic textures per board layer, divide each layer into a uniform 2D grid of fixed-size chunk textures (e.g., $1024 \times 1024$ pixels).

| Metric | Monolithic Canvas ($3000 \times 3000$) | Chunk Grid ($1024 \times 1024$ Chunks) |
| --- | --- | --- |
| **Texture Allocations** | 2 textures ($3000 \times 3000$) | 18 textures ($3 \times 3$ grid $\times 2$ layers) |
| **Max Allocation Dimension** | $3000\text{ px}$ (scales unboundedly) | $1024\text{ px}$ (fixed, hardware-safe) |
| **Visible Draw Calls** | 2 `SDL_RenderCopy` calls | 4–6 `SDL_RenderCopy` calls per frame |
| **Seasonal Re-bake Cost** | Full board ($3000 \times 3000$) | Per-chunk on-demand or background queue |

---

### 2. Implementation Architecture

#### A. Chunk Data Structure

Represent each spatial partition as a container holding the baked background and foreground `TexturePtr` instances:

```python
from dataclasses import dataclass
from typing import Dict, Tuple, List
from libs.graphics.registry import TexturePtr

CHUNK_SIZE = 1024

@dataclass(slots=True)
class CanvasChunk:
    cx: int
    cy: int
    bg: TexturePtr
    fg: TexturePtr
    dirty: bool = False

```

#### B. Chunk Partitioning and Pre-rendering (`Screen._prerender`)

When building tile tuples, bucket them by their intersecting chunk grid coordinates `(cx, cy)`:

```python
def _bucket_tiles_by_chunk(
    self, 
    tiles: List[Asset], 
    calendar: CalendarState, 
    chunk_size: int = CHUNK_SIZE
) -> Dict[Tuple[int, int], Tuple[list, list]]:
    """
    Groups tile render tuples into discrete (cx, cy) chunks.
    Coordinates are translated relative to each chunk's origin (0, 0).
    """
    buckets: Dict[Tuple[int, int], Tuple[list, list]] = {}

    for tile in tiles:
        frame_keys = tile.frame.eras(tile.id, calendar)
        for frame_key, ox, oy in frame_keys:
            tex_data = self.registry.image(frame_key)
            if not tex_data:
                continue

            tex, sx, sy, sw, sl = tex_data
            abs_x = tile.state.position.x + ox
            abs_y = tile.state.position.y + oy
            tile_w = tile.dimensions.w
            tile_l = tile.dimensions.l
            nx = tile.state.multiple.nx
            ny = tile.state.multiple.ny

            # Determine chunk range covered by this tile
            min_cx = abs_x // chunk_size
            max_cx = (abs_x + (nx * tile_w) - 1) // chunk_size
            min_cy = abs_y // chunk_size
            max_cy = (abs_y + (ny * tile_l) - 1) // chunk_size

            for cx in range(min_cx, max_cx + 1):
                for cy in range(min_cy, max_cy + 1):
                    key = (cx, cy)
                    if key not in buckets:
                        buckets[key] = ([], [])

                    # Local origin translation inside the chunk
                    chunk_origin_x = cx * chunk_size
                    chunk_origin_y = cy * chunk_size

                    tile_tuple = (
                        tex, sx, sy, sw, sl,
                        abs_x - chunk_origin_x,
                        abs_y - chunk_origin_y,
                        tile_w, tile_l,
                        nx, ny,
                    )

                    if tile.taxonomy.instance == AssetInstances.ENVIRON.value:
                        buckets[key][0].append(tile_tuple)
                    elif tile.taxonomy.instance == AssetInstances.CANOPY.value:
                        buckets[key][1].append(tile_tuple)

    return buckets

```

#### C. Baking Chunks in `Screen`

Initialize chunks across the board boundaries:

```python
class ChunkedScreen:
    chunks: Dict[Tuple[int, int], CanvasChunk]

    def _bake_chunks(self, tiles: List[Asset], calendar: CalendarState):
        buckets = self._bucket_tiles_by_chunk(tiles, calendar)
        max_cx = (self.boardsize.w + CHUNK_SIZE - 1) // CHUNK_SIZE
        max_cy = (self.boardsize.l + CHUNK_SIZE - 1) // CHUNK_SIZE

        self.chunks = {}
        for cx in range(max_cx):
            for cy in range(max_cy):
                # Only allocate textures for chunks that contain tiles or viewport coverage
                bg = render.canvas(CHUNK_SIZE, CHUNK_SIZE, opaque=(len(tiles) == 0))
                fg = render.canvas(CHUNK_SIZE, CHUNK_SIZE)

                back_tiles, fore_tiles = buckets.get((cx, cy), ([], []))
                if back_tiles:
                    render.construct(bg, back_tiles)
                if fore_tiles:
                    render.construct(fg, fore_tiles)

                self.chunks[(cx, cy)] = CanvasChunk(cx=cx, cy=cy, bg=bg, fg=fg)

```

#### D. Viewport-Culled Rendering (`render_chunks`)

During `Screen.draw()`, calculate camera bounds and only blit chunks that intersect `[pov.x, pov.x + screensize.w]` and `[pov.y, pov.y + screensize.l]`:

```python
def _render_background_chunks(self, pov: Position) -> None:
    cdef int chunk_size = CHUNK_SIZE
    cdef int min_cx = max(0, pov.x // chunk_size)
    cdef int max_cx = min((self.boardsize.w - 1) // chunk_size, (pov.x + self.screensize.w) // chunk_size)
    cdef int min_cy = max(0, pov.y // chunk_size)
    cdef int max_cy = min((self.boardsize.l - 1) // chunk_size, (pov.y + self.screensize.l) // chunk_size)

    cdef SDL_Rect src_rect, dst_rect
    cdef int cx, cy, chunk_x, chunk_y

    for cx in range(min_cx, max_cx + 1):
        for cy in range(min_cy, max_cy + 1):
            chunk = self.chunks.get((cx, cy))
            if not chunk:
                continue

            chunk_x = cx * chunk_size
            chunk_y = cy * chunk_size

            # Intersect chunk with camera view
            src_rect.x = max(0, pov.x - chunk_x)
            src_rect.y = max(0, pov.y - chunk_y)
            src_rect.w = min(chunk_size - src_rect.x, (pov.x + self.screensize.w) - (chunk_x + src_rect.x))
            src_rect.h = min(chunk_size - src_rect.y, (pov.y + self.screensize.l) - (chunk_y + src_rect.y))

            dst_rect.x = (chunk_x + src_rect.x) - pov.x
            dst_rect.y = (chunk_y + src_rect.y) - pov.y
            dst_rect.w = src_rect.w
            dst_rect.h = src_rect.h

            # Blit chunk background to renderer
            SDL_RenderCopy(_renderer, chunk.bg.ptr, &src_rect, &dst_rect)

```

---

### 3. Handling Full Board Exports (`export_map`)

For `export_map()`, allocating a transient target texture matching arbitrary board dimensions ($>8000 \times 8000$) will fail if it exceeds the driver's maximum render target bounds.

Replace full-board VRAM allocation with an **iterative tile stitcher** directly into a client-side surface:

1. Allocate a single CPU-side `SDL_Surface*` via `SDL_CreateRGBSurfaceWithFormat(0, boardsize.w, boardsize.l, 32, SDL_PIXELFORMAT_RGBA32)`.
2. Allocate a single reusable $1024 \times 1024$ GPU render target (`render.canvas(1024, 1024)`).
3. Loop over the chunk grid:
* Render the chunk background, foreground, and culled active assets into the $1024 \times 1024$ target.
* Use `SDL_RenderReadPixels` to read the $1024 \times 1024$ block into host RAM.
* Blit that block into the destination CPU `SDL_Surface` at `(cx * 1024, cy * 1024)` via `SDL_BlitSurface`.


4. Call `IMG_SavePNG(full_surface, b_filename)` and free the CPU surface.

---

### Immediate Implementation Checklist

1. **Verify Driver Texture Limits:** Call `sysinfo()` during engine boot to assert that `CHUNK_SIZE` ($\le 1024$) is strictly less than `info.max_texture_width` and `info.max_texture_height`.
2. **Refactor `Screen` Storage:** Replace `self.bg_canvas` and `self.fg_canvas` attributes with a dictionary `self.chunks: Dict[Tuple[int, int], CanvasChunk]`.
3. **Update Memory Release:** In `Screen.destroy()`, iterate through `self.chunks.values()` and call `render.destroy()` on both `chunk.bg` and `chunk.fg` to avoid VRAM leaks.
4. **Update `reconstruct()`:** Only re-bake chunks marked as dirty or those containing tiles affected by the incoming calendar mutation.