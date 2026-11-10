"""
@domain.test
@test.unit
@app.library
@app.asset
@asset.frame
@workflow.rendering

# Ontology: Tests - tests.unit.libs.graphics.test_registry

Unit tests for the Registry class.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Fonts,
)
from app.static.settings import SEPARATOR

# Cython Libraries
from libs.graphics.registry import (
    TexturePtr,
    TTFFont,
)

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_library,
    pytest.mark.workflow_rendering,
]

# -----------------------------------------------------


def test_registry_initialization_and_caching(mock_registry):
    """
    Verify Registry discovers asset filepaths, indexes frame crop maps,
    populates the prewarm queue, and defers VRAM texture allocation at boot.
    """
    assert len(mock_registry._filepaths) > 0
    assert len(mock_registry._pending_assets) > 0
    assert len(mock_registry._frames) > 0
    assert mock_registry.maximum == len(mock_registry._pending_assets)
    assert mock_registry.current == 0
    assert len(mock_registry._textures) == 0
    assert len(mock_registry._fonts) == 0


@pytest.mark.app_asset
@pytest.mark.asset_frame
def test_registry_indexing_and_retrieval(mock_registry, mock_asset):
    """
    Verify Registry retrieves indexed frame crop coordinates, JIT-loads
    textures into the cache upon first request, and serves subsequent requests
    from the texture cache.
    """
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
        id="temperate",
    )
    frame_key = f"{tile.id}{SEPARATOR}spring{SEPARATOR}onset{SEPARATOR}0"

    assert frame_key in mock_registry._frames
    assert tile.id not in mock_registry._textures

    first_data = mock_registry.image(frame_key)
    second_data = mock_registry.image(frame_key)

    assert first_data is not None
    assert first_data == second_data
    assert tile.id in mock_registry._textures
    assert first_data[0] is mock_registry._textures[tile.id]
    assert first_data[1:] == (0, 0, tile.dimensions.w, tile.dimensions.l)
    assert mock_registry.image("nonexistent-frame-key") is None


def test_registry_fallback_retrieval_and_non_png_rejection(mock_registry):
    """
    Verify Registry falls back to full texture dimensions for unindexed PNG
    assets in _filepaths and rejects non-PNG filepaths during image lookup.
    """
    raw_id = "unindexed_raw_tile"
    mock_registry._filepaths[raw_id] = "/mock/assets/unindexed_raw_tile.png"

    assert raw_id not in mock_registry._frames
    assert raw_id not in mock_registry._textures

    data = mock_registry.image(raw_id)

    assert data is not None
    assert raw_id in mock_registry._textures
    tex = data[0]
    assert data == (tex, 0, 0, tex.w, tex.l)

    # Non-PNG filepath should not load as an image texture
    font_key = Fonts.DIALOGUE.value
    assert mock_registry.image(font_key) is None


@pytest.mark.category_sheets
def test_registry_stack_assembly(mock_registry, mock_render, mock_asset):
    """
    Verify Registry JIT-compiles stacked Sheet assets via render.compose and
    caches the composed texture.
    """
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    frame_key, _, _ = player.frame.keys(player.id, player.state)[0]

    assert player.id in mock_registry._stacks
    assert player.id not in mock_registry._textures

    data = mock_registry.image(frame_key)

    assert data is not None
    assert player.id in mock_registry._textures
    mock_render.compose.assert_called_once()
    base_tex, overlay_texs = mock_render.compose.call_args[0]
    expected_overlays = [
        layer
        for layer in player.properties.stack[1:]
        if layer in mock_registry._filepaths
    ]
    assert base_tex is not None
    assert len(overlay_texs) == len(expected_overlays)


@pytest.mark.category_sheets
def test_registry_stack_single_layer_and_missing_base(mock_registry, mock_render, mock_asset):
    """
    Verify Registry returns the base texture directly without calling
    render.compose when a stack has no valid overlays, and returns None when
    the stack's base layer cannot be resolved.
    """
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    base_layer = player.properties.stack[0]

    # 1. Single-layer stack (no overlays) bypasses render.compose
    mock_registry._stacks["single_stack"] = [base_layer]
    single_data = mock_registry.image("single_stack")

    assert single_data is not None
    assert "single_stack" in mock_registry._textures
    mock_render.compose.assert_not_called()

    # 2. Missing base layer returns None
    mock_registry._stacks["broken_stack"] = ["nonexistent_base_layer"]
    assert mock_registry.image("broken_stack") is None
    assert "broken_stack" not in mock_registry._textures


@pytest.mark.category_sheets
def test_registry_cyclic_stack_resolution(mock_registry, mock_render, mock_asset):
    """
    Verify Registry breaks self-referential stack cycles when an asset ID exists
    in both _stacks and _filepaths.
    """
    player = mock_asset(
        AssetCategories.SHEETS.value,
        AssetInstances.PLAYERS.value,
    )
    overlay_id = player.properties.stack[0]
    mock_registry._filepaths[player.id] = "/mock/assets/player.png"
    mock_registry._stacks[player.id] = [player.id, overlay_id]

    data = mock_registry.image(player.id)

    assert data is not None
    assert player.id in mock_registry._textures
    mock_render.compose.assert_called_once()
    _, overlay_texs = mock_render.compose.call_args[0]
    assert len(overlay_texs) == 1


def test_registry_prewarm_budget(monkeypatch, mock_registry):
    """
    Verify prewarming yields False when the frame time budget is exceeded and
    returns True once the pending asset queue is exhausted.
    """
    total_pending = mock_registry.maximum
    assert total_pending > 0
    assert mock_registry.current == 0

    # 1. Exceed budget immediately on first iteration check
    ticks = iter([0.0, 0.020])
    monkeypatch.setattr(
        "libs.graphics.registry.time.perf_counter",
        lambda: next(ticks),
    )
    done = mock_registry.prewarm(budget_ms=10)
    assert done is False
    assert mock_registry.current == 0
    assert len(mock_registry._pending_assets) == total_pending

    # 2. Exhaust queue within budget
    monkeypatch.setattr(
        "libs.graphics.registry.time.perf_counter",
        lambda: 0.0,
    )
    done = mock_registry.prewarm(budget_ms=10)
    assert done is True
    assert mock_registry.current == total_pending
    assert len(mock_registry._pending_assets) == 0


@pytest.mark.workflow_typography
def test_registry_font_loading_and_retrieval(mock_registry):
    """
    Verify Registry lazily loads and caches configured TTFFont instances.
    """
    font_key = Fonts.DIALOGUE.value
    assert font_key in mock_registry._filepaths
    assert font_key not in mock_registry._fonts

    retrieved_font = mock_registry.font(font_key)

    assert isinstance(retrieved_font, TTFFont)
    assert font_key in mock_registry._fonts
    assert mock_registry.font(font_key) is retrieved_font


@pytest.mark.workflow_typography
def test_registry_missing_and_unconfigured_font(mock_registry):
    """
    Verify font retrieval returns None for both unknown font keys and .ttf files
    present in _filepaths that lack a corresponding FontProperties entry.
    """
    assert mock_registry.font("missing_font") is None

    unconfigured_key = "unconfigured_ttf_font"
    mock_registry._filepaths[unconfigured_key] = "/mock/assets/unconfigured_ttf_font.ttf"

    assert mock_registry.font(unconfigured_key) is None
    assert unconfigured_key not in mock_registry._fonts


def test_registry_clear_releases_caches(monkeypatch, mock_registry):
    """
    Verify Registry.clear empties all cached textures, fonts, frames, stacks,
    and pending asset queues.
    """
    monkeypatch.setattr(
        "libs.graphics.registry._sys_load_image",
        lambda *args, **kwargs: TexturePtr(),
    )
    mock_registry.image("temperate-spring-onset-0")
    mock_registry.font(Fonts.DIALOGUE.value)

    assert len(mock_registry._textures) > 0
    assert len(mock_registry._fonts) > 0
    assert len(mock_registry._frames) > 0
    assert len(mock_registry._stacks) > 0

    mock_registry.clear()

    assert len(mock_registry._textures) == 0
    assert len(mock_registry._fonts) == 0
    assert len(mock_registry._frames) == 0
    assert len(mock_registry._stacks) == 0
    assert len(mock_registry._pending_assets) == 0