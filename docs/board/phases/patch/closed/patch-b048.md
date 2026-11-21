
##### Bug B048: Outlined Text Glyph Misalignment & Missing Vertical Offset in `render.write`

**STATUS**: CLOSED
**SEVERITY**: MEDIUM

**Description**

In `src/libs/graphics/render.pyx` (`write`, lines 354–439):
1. When rendering outlined text (`font.outline_ptr != NULL and font.outline_width > 0`), `TTF_RenderUTF8_Blended_Wrapped` is called on the entire string `b_content` using `font.outline_ptr` (which has `TTF_SetFontOutline` applied), and the resulting surface is stamped once at `outline_rect.x = dst_rect.x - font.outline_width`. In `SDL2_ttf`, `TTF_SetFontOutline` increases the width and horizontal advance of **each individual glyph** by `2 * outline_width`. For a line of $N$ characters, the outlined surface is wider by $2 \cdot N \cdot \text{outline\_width}$ pixels, causing every character after the first to drift progressively further right relative to `text_surface` and causing multi-line text to wrap at different word boundaries.
2. `dst_rect.y = margin_px_h` omits the target crop offset `sy` (unlike `dst_rect.x`, which adds `sx`).

**Steps to Replicate** 

1. Configure a `Font` in `/src/assets/fonts/**/*.yaml` with `outline.width: 2` and render a multi-character string onto a `Pane` via `Screen.stamp`.
2. Observe that the outline aligns with the first character on the left, but shifts progressively to the right by `2 * outline_width` pixels per character across the string.

**Proposed Remeditation**

To outline wrapped text accurately in `SDL2_ttf`, either:
* Stamp `text_tex` (or `text_surface` rendered in `outline_color` using the base `font.ptr`) at 8-directional offsets $(\pm w, \pm w)$ behind the foreground `text_tex`, which guarantees identical glyph advances and word-wrapping bounds; or
* Render glyph-by-glyph using `TTF_GlyphMetrics` advances from the base font.
Additionally, set `dst_rect.y = sy + margin_px_h`.