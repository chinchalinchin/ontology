"""
@domain.test
@domain.graphics
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
from libs.graphics.registry import TTFFont

# -----------------------------------------------------

pytestmark = [
    pytest.mark.libs_graphics,
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
    Verify Registry retrieves indexed frame crop coordinates and JIT-loads
    textures into the cache upon request.
    """
    tile = mock_asset(
        AssetCategories.TILES.value,
        AssetInstances.ENVIRON.value,
        id="temperate",
    )
    frame_key = f"{tile.id}{SEPARATOR}spring{SEPARATOR}onset{SEPARATOR}0"

    assert frame_key in mock_registry._frames
    assert tile.id not in mock_registry._textures

    data = mock_registry.image(frame_key)

    assert data is not None
    assert tile.id in mock_registry._textures
    assert data[0] == mock_registry._textures[tile.id]
    assert data[1:] == (0, 0, tile.dimensions.w, tile.dimensions.l)
    assert mock_registry.image("nonexistent-frame-key") is None


def test_registry_fallback_retrieval(mock_registry):
    """
    Verify Registry falls back to full texture dimensions for unindexed assets
    present in _filepaths.
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
    assert base_tex is not None
    assert len(overlay_texs) == len(player.properties.stack) - 1


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
    assert mock_registry.font(font_key) == retrieved_font


@pytest.mark.workflow_typography
def test_registry_missing_font(mock_registry):
    """
    Verify font retrieval for an unindexed font key returns None.
    """
    assert mock_registry.font("missing_font") is None