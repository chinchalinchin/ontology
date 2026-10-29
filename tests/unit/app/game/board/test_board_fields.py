"""
@domain.test
@test.unit
@app.board
@app.core
@app.component
@physics.fields
@workflow.fluids
@workflow.ecology

# Ontology: Tests - tests.unit.app.game.board.test_board_fields

Unit tests verifying continuous MoistureField potential modeling,
distance attenuation, superposition, and Board-level flux caching.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
from app.static.semantics import AssetInstances

# Cython Libraries
from libs.core.models import Position

# -----------------------------------------------------

pytestmark = [
    pytest.mark.app_board,
    pytest.mark.app_core,
    pytest.mark.app_component,
    pytest.mark.physics_fields,
    pytest.mark.workflow_fluids,
    pytest.mark.workflow_ecology,
]

# -----------------------------------------------------


def test_moisture_field_linear_stream_attenuation(mock_moisture_field):
    """
    Verify linear stream corridors produce exponential moisture attenuation
    as orthogonal distance increases.
    """
    mock_moisture_field.sigma = 64.0
    mock_moisture_field.phi_0 = 1.0
    mock_moisture_field.add_stream(100.0, 100.0, 100.0, 200.0, flow=2)

    # Exact on-axis sample: dist = 0 -> phi = phi_0 * flow * exp(0) = 2.0
    on_axis = mock_moisture_field.evaluate(100.0, 150.0)
    assert on_axis == pytest.approx(2.0, rel=1e-3)

    # Transverse offset: dist = 32 -> phi = 2.0 * exp(-32 / 64) = 2.0 * exp(-0.5)
    offset_32 = mock_moisture_field.evaluate(132.0, 150.0)
    expected_32 = 2.0 * math.exp(-32.0 / 64.0)
    assert offset_32 == pytest.approx(expected_32, rel=1e-3)

    # Beyond cutoff: cutoff = sigma * flow = 64 * 2 = 128 -> dist=150 receives 0.0
    beyond_cutoff = mock_moisture_field.evaluate(250.0, 150.0)
    assert beyond_cutoff == 0.0


def test_moisture_field_annular_pool_radial_attenuation(mock_moisture_field):
    """
    Verify annular pool disks produce radial exponential attenuation
    outside the pool radius and maximum potential inside the disk.
    """
    mock_moisture_field.sigma = 64.0
    mock_moisture_field.phi_0 = 1.0
    cx, cy, radius, flow = 200.0, 200.0, 30.0, 1
    mock_moisture_field.add_pool(cx, cy, radius, flow)

    # Inside pool boundary: dist_to_center <= radius -> dist = 0 -> phi = 1.0
    inside = mock_moisture_field.evaluate(210.0, 200.0)
    assert inside == pytest.approx(1.0, rel=1e-3)

    # Edge of pool: dist_to_center = 30 -> dist = 0 -> phi = 1.0
    edge = mock_moisture_field.evaluate(230.0, 200.0)
    assert edge == pytest.approx(1.0, rel=1e-3)

    # Radial offset: dist_to_center = 50 -> dist = 20 -> phi = 1.0 * exp(-20 / 64)
    outside_20 = mock_moisture_field.evaluate(250.0, 200.0)
    expected = math.exp(-20.0 / 64.0)
    assert outside_20 == pytest.approx(expected, rel=1e-3)

    # Beyond cutoff: cutoff = 64 * 1 = 64 -> dist = 70 (center offset 100) -> 0.0
    beyond = mock_moisture_field.evaluate(300.0, 200.0)
    assert beyond == 0.0


def test_moisture_field_linear_superposition(mock_moisture_field):
    """
    Verify multiple stream corridors and pools sum linearly by superposition.
    """
    mock_moisture_field.sigma = 64.0
    mock_moisture_field.phi_0 = 1.0
    # Stream 1: on-axis at (100, 100) with flow 1 -> contribution = 1.0
    mock_moisture_field.add_stream(100.0, 0.0, 100.0, 200.0, flow=1)
    # Stream 2: on-axis at (100, 100) with flow 2 -> contribution = 2.0
    mock_moisture_field.add_stream(0.0, 100.0, 200.0, 100.0, flow=2)

    total = mock_moisture_field.evaluate(100.0, 100.0)
    assert total == pytest.approx(3.0, rel=1e-3)


def test_board_set_moisture_field_precomputes_resource_flux(
    mock_board,
    mock_moisture_field,
):
    """
    Verify Board.set_moisture_field caches the field and precomputes
    moisture_flux on static resource instances.
    """
    resource = mock_board.instances(AssetInstances.CROPS.value, "0")[0]
    resource.state.position = Position(x=100, y=100)

    mock_moisture_field.sigma = 64.0
    mock_moisture_field.phi_0 = 1.0
    mock_moisture_field.add_stream(100.0, 0.0, 100.0, 200.0, flow=2)

    mock_board.set_moisture_field("0", mock_moisture_field)

    # Resource at (100, 100) is directly on-axis with flow 2 -> flux = 2.0
    assert resource.state.moisture_flux == pytest.approx(2.0, rel=1e-3)
    assert mock_board.moisture("0", 100, 100) == pytest.approx(2.0, rel=1e-3)


def test_board_moisture_query_unpopulated_layer(mock_board):
    """
    Verify querying moisture on a layer without an active field returns 0.0.
    """
    assert mock_board.moisture("unpopulated-layer", 50, 50) == 0.0