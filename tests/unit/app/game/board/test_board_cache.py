"""
@domain.test
@test.unit
@app.board
@app.component
@workflow.collisions

# Ontology: Tests - tests.unit.app.game.board.test_cache_partitioning

Unit tests for Phase 03.07 static/dynamic weight partitioning, versioned invalidation,
and normalized obstacle queries on Board and Cache.
"""
# External Libraries
import pytest

# Application Libraries
import app.game.logic.predicates as predicates
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Buildings,
    EffectsPalette,
    LayerProjections,
)

# Cython Libraries
from libs.core.models import Position

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.app_board,
    pytest.mark.app_component,
    pytest.mark.workflow_collisions,
]

# ---------------------------------------------------------------------------


def test_board_weights_disjoint_partition_between_dynamics_and_statics(mock_board):
    """
    Verifies Board.dynamics(layer) (m > 0) and Board.statics(layer) (m == 0)
    form an exact disjoint partition of Board.weights(layer).
    """
    for layer in mock_board.layers():
        weights = set(mock_board.weights(layer))
        dynamics = set(mock_board.dynamics(layer))
        statics = set(mock_board.statics(layer))

        assert dynamics.isdisjoint(statics)
        assert dynamics | statics == weights
        assert all(a.properties.mass > 0 for a in dynamics)
        assert all(a.properties.mass == 0 for a in statics)

    # Layerless aggregation matches union across all layers
    all_dynamics = set(mock_board.dynamics())
    all_statics = set(mock_board.statics())
    assert all_dynamics.isdisjoint(all_statics)
    assert all_dynamics | all_statics == set(mock_board.weights())


def test_board_invalidate_statics_reindexes_gate_switch_state(mock_board):
    """
    Verifies toggling a Gate's switch and calling invalidate_statics removes it
    from tier-indexed statics when open and restores it when closed.
    """
    gate = mock_board.instances(AssetInstances.GATES.value)[0]
    layer = gate.state.layer
    gate.elevation = 0

    gate.state.switch = False
    mock_board.invalidate_statics(layer)
    assert gate in mock_board.statics(layer, elevation=0)

    gate.state.switch = True
    mock_board.invalidate_statics(layer)
    assert gate not in mock_board.statics(layer, elevation=0)
    # Retained in layer static_weights so closing re-indexes it on next rebuild
    assert gate in mock_board.statics(layer)

    gate.state.switch = False
    mock_board.invalidate_statics(layer)
    assert gate in mock_board.statics(layer, elevation=0)


def test_board_obstacles_aggregates_all_layers_when_layer_is_none(
    mock_board,
    mock_asset,
):
    """
    Verifies Board.obstacles(layer=None) aggregates obstacles across every layer
    and supports optional elevation filtering.
    """
    extra_layer = "obstacles-extra-layer"
    extra_chest = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    extra_chest.taxonomy.name = "extra-layer-chest"
    extra_chest.state.name = "extra-layer-chest"
    extra_chest.state.layer = extra_layer
    extra_chest.elevation = 1
    mock_board.add([extra_chest])

    per_layer_union = set()
    for layer in mock_board.layers():
        per_layer_union.update(mock_board.obstacles(layer))

    all_obstacles = set(mock_board.obstacles())
    assert all_obstacles == per_layer_union
    assert extra_chest in all_obstacles
    assert extra_chest in mock_board.obstacles(elevation=1)
    assert extra_chest not in mock_board.obstacles(elevation=0)


def test_board_statics_and_dynamics_elevation_filtering(mock_board, mock_asset):
    """
    Verifies elevation filtering normalizes negative tiers to 0 and isolates
    higher elevation tiers across Board.statics and Board.dynamics.
    """
    layer = mock_board.player().state.layer
    elevated_gate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    elevated_gate.taxonomy.name = "elev-gate"
    elevated_gate.state.name = "elev-gate"
    elevated_gate.state.layer = layer
    elevated_gate.state.switch = False
    elevated_gate.elevation = 2

    elevated_crate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    elevated_crate.taxonomy.name = "elev-crate"
    elevated_crate.state.name = "elev-crate"
    elevated_crate.state.layer = layer
    elevated_crate.elevation = 2

    mock_board.add([elevated_gate, elevated_crate])

    assert elevated_gate in mock_board.statics(layer, elevation=2)
    assert elevated_gate not in mock_board.statics(layer, elevation=0)
    assert elevated_gate in mock_board.statics(elevation=2)

    assert elevated_crate in mock_board.dynamics(layer, elevation=2)
    assert elevated_crate not in mock_board.dynamics(layer, elevation=0)

    # Negative elevation queries collapse to tier 0
    assert mock_board.statics(layer, elevation=-1) == mock_board.statics(layer, elevation=0)
    assert mock_board.dynamics(layer, elevation=-1) == mock_board.dynamics(layer, elevation=0)


def test_board_static_version_invalidation_and_transient_exclusion(
    mock_board,
    mock_asset,
):
    """
    Verifies Board.static_version increments on static mutations and explicit
    invalidate_statics calls, while ignoring dynamic bodies and transient passive effects.
    """
    layer = mock_board.player().state.layer
    v0 = mock_board.static_version(layer)

    # Dynamic bodies (crates and pushable chests) add/remove do not bump static_version
    dyn_crate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    dyn_crate.taxonomy.name = "transient-crate"
    dyn_crate.state.name = "transient-crate"
    dyn_crate.state.layer = layer
    mock_board.add([dyn_crate])
    assert mock_board.static_version(layer) == v0

    mock_board.remove([dyn_crate])
    assert mock_board.static_version(layer) == v0

    dyn_chest = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    dyn_chest.taxonomy.name = "transient-chest"
    dyn_chest.state.name = "transient-chest"
    dyn_chest.state.layer = layer
    mock_board.add([dyn_chest])
    assert mock_board.static_version(layer) == v0
    mock_board.remove([dyn_chest])
    assert mock_board.static_version(layer) == v0

    # Passive splash add/remove does not bump static_version
    splash = mock_board.cradle.spawn_passive(
        EffectsPalette.SPLASH.value,
        layer,
        Position(5000, 5000),
    )
    mock_board.add([splash])
    assert mock_board.static_version(layer) == v0
    mock_board.remove([splash])
    assert mock_board.static_version(layer) == v0

    # Static body (closed Gate, m == 0) add/remove increments static_version and updates statics index
    gate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    gate.taxonomy.name = "versioned-gate"
    gate.state.name = "versioned-gate"
    gate.state.layer = layer
    gate.state.switch = False
    gate.elevation = 0
    mock_board.add([gate])
    v1 = mock_board.static_version(layer)
    assert v1 > v0
    assert gate in mock_board.statics(layer, elevation=0)

    mock_board.remove([gate])
    v2 = mock_board.static_version(layer)
    assert v2 > v1
    assert gate not in mock_board.statics(layer, elevation=0)

    # Explicit invalidate_statics(layer) and invalidate_statics(None) increment version
    mock_board.invalidate_statics(layer)
    v3 = mock_board.static_version(layer)
    assert v3 > v2

    mock_board.invalidate_statics()
    assert mock_board.static_version(layer) > v3


def test_board_relayer_updates_static_and_dynamic_caches(mock_board, mock_asset):
    """
    Verifies relayering updates statics/dynamics partitions and bumps static_version
    on both source and destination layers only for static-affecting assets.
    """
    src_layer = mock_board.player().state.layer
    dst_layer = "relayer-target-layer"

    gate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    gate.taxonomy.name = "relayer-gate"
    gate.state.name = "relayer-gate"
    gate.state.layer = src_layer
    gate.state.switch = False
    gate.elevation = 0

    crate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CRATES.value)
    crate.taxonomy.name = "relayer-crate"
    crate.state.name = "relayer-crate"
    crate.state.layer = src_layer
    crate.elevation = 0

    mock_board.add([gate, crate])
    v_src_before = mock_board.static_version(src_layer)
    v_dst_before = mock_board.static_version(dst_layer)

    # Relayering dynamic crate leaves static_version untouched
    mock_board.relayer(crate, dst_layer)
    assert crate not in mock_board.dynamics(src_layer)
    assert crate in mock_board.dynamics(dst_layer)
    assert mock_board.static_version(src_layer) == v_src_before
    assert mock_board.static_version(dst_layer) == v_dst_before

    # Relayering static gate bumps both layers and migrates elevation index
    mock_board.relayer(gate, dst_layer)
    assert gate not in mock_board.statics(src_layer, elevation=0)
    assert gate in mock_board.statics(dst_layer, elevation=0)
    assert mock_board.static_version(src_layer) > v_src_before
    assert mock_board.static_version(dst_layer) > v_dst_before


def test_predicates_is_weight_excludes_passable_crafts_and_door_sensors(
    mock_asset,
    mock_board,
):
    """
    Verifies predicates.is_weight excludes passable MaterialHitbox floor struts
    and sensor Doors (both IN and OUT projections), while retaining solid static
    and dynamic weights.
    """
    floor_strut = mock_asset(AssetCategories.CRAFTS.value, AssetInstances.STRUTS.value)
    floor_strut.state.blueprint = Buildings.FLOORS.value
    assert predicates.is_weight(floor_strut) is False

    door = mock_board.instances(AssetInstances.DOORS.value)[0]
    door.state.projection = LayerProjections.OUT.value
    assert predicates.is_weight(door) is False

    door.state.projection = LayerProjections.IN.value
    assert predicates.is_weight(door) is False

    gate = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.GATES.value)
    gate.state.switch = False
    assert predicates.is_weight(gate) is True

    chest = mock_asset(AssetCategories.OBJECTS.value, AssetInstances.CHESTS.value)
    assert predicates.is_weight(chest) is True