"""
# Ontology: tests.unit.app.game.board.test_board_fields

Unit tests verifying continuous MoistureField potential modeling,
distance attenuation, superposition, and Board-level flux caching.
"""
# Standard Libraries
import math

# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    AssetCategories,
    Lifespans
)
from app.game.board.fields import MoistureField
from app.models.properties import ResourceProperties
from app.models.state import ResourceState
from app.assets.base import Asset, Taxonomy
from app.assets.frames import StageFrame
from app.assets.animations import NoAnimation

# Cython Libraries
from libs.core.models import Position, Dimensions


@pytest.mark.ecology
@pytest.mark.fluids
@pytest.mark.seasons
def test_moisture_field_linear_stream_attenuation():
    """
    Verify linear stream corridors produce exponential moisture attenuation
    as orthogonal distance increases.
    """
    field = MoistureField(sigma=64.0, phi_0=1.0)
    field.add_stream(100.0, 100.0, 100.0, 200.0, flow=2)

    # Exact on-axis sample: dist = 0 -> phi = phi_0 * flow * exp(0) = 2.0
    on_axis = field.evaluate(100.0, 150.0)
    assert on_axis == pytest.approx(2.0, rel=1e-3)

    # Transverse offset: dist = 32 -> phi = 2.0 * exp(-32 / 64) = 2.0 * exp(-0.5)
    offset_32 = field.evaluate(132.0, 150.0)
    expected_32 = 2.0 * math.exp(-32.0 / 64.0)
    assert offset_32 == pytest.approx(expected_32, rel=1e-3)

    # Beyond cutoff: cutoff = sigma * flow = 64 * 2 = 128 -> dist=150 receives 0.0
    beyond_cutoff = field.evaluate(250.0, 150.0)
    assert beyond_cutoff == 0.0


@pytest.mark.ecology
@pytest.mark.fluids
@pytest.mark.seasons
def test_moisture_field_annular_pool_radial_attenuation():
    """
    Verify annular pool disks produce radial exponential attenuation
    outside the pool radius and maximum potential inside the disk.
    """
    field = MoistureField(sigma=64.0, phi_0=1.0)
    cx, cy, radius, flow = 200.0, 200.0, 30.0, 1
    field.add_pool(cx, cy, radius, flow)

    # Inside pool boundary: dist_to_center <= radius -> dist = 0 -> phi = 1.0
    inside = field.evaluate(210.0, 200.0)
    assert inside == pytest.approx(1.0, rel=1e-3)

    # Edge of pool: dist_to_center = 30 -> dist = 0 -> phi = 1.0
    edge = field.evaluate(230.0, 200.0)
    assert edge == pytest.approx(1.0, rel=1e-3)

    # Radial offset: dist_to_center = 50 -> dist = 20 -> phi = 1.0 * exp(-20 / 64)
    outside_20 = field.evaluate(250.0, 200.0)
    expected = math.exp(-20.0 / 64.0)
    assert outside_20 == pytest.approx(expected, rel=1e-3)

    # Beyond cutoff: cutoff = 64 * 1 = 64 -> dist = 70 (center offset 100) -> 0.0
    beyond = field.evaluate(300.0, 200.0)
    assert beyond == 0.0


@pytest.mark.ecology
@pytest.mark.fluids
@pytest.mark.seasons
def test_moisture_field_linear_superposition():
    """
    Verify multiple stream corridors and pools sum linearly by superposition.
    """
    field = MoistureField(sigma=64.0, phi_0=1.0)
    # Stream 1: on-axis at (100, 100) with flow 1 -> contribution = 1.0
    field.add_stream(100.0, 0.0, 100.0, 200.0, flow=1)
    # Stream 2: on-axis at (100, 100) with flow 2 -> contribution = 2.0
    field.add_stream(0.0, 100.0, 200.0, 100.0, flow=2)

    total = field.evaluate(100.0, 100.0)
    assert total == pytest.approx(3.0, rel=1e-3)


@pytest.mark.ecology
@pytest.mark.fluids
@pytest.mark.seasons
def test_board_set_moisture_field_precomputes_resource_flux(mock_board):
    """
    Verify Board.set_moisture_field caches the field and precomputes
    moisture_flux on static resource instances.
    """
    resource = Asset(
        taxonomy=Taxonomy(
            id="maize",
            name="cornfield-test",
            category=AssetCategories.RESOURCES.value,
            instance="crops"
        ),
        properties=ResourceProperties(
            dimensions=Dimensions(w=32, l=32),
            loot="maize",
            lifespan=Lifespans.ANNUAL.value,
            mass=0
        ),
        state=ResourceState(
            id="maize",
            layer="0",
            position=Position(x=100, y=100),
            retention=0.0,
            moisture_flux=0.0
        ),
        frame=StageFrame(),
        animation=NoAnimation()
    )

    mock_board.clear()
    mock_board.add([resource])

    field = MoistureField(sigma=64.0, phi_0=1.0)
    field.add_stream(100.0, 0.0, 100.0, 200.0, flow=2)

    mock_board.set_moisture_field("0", field)

    # Resource at (100, 100) is directly on-axis with flow 2 -> flux = 2.0
    assert resource.state.moisture_flux == pytest.approx(2.0, rel=1e-3)
    # Board.moisture query matches
    assert mock_board.moisture("0", 100, 100) == pytest.approx(2.0, rel=1e-3)


@pytest.mark.ecology
@pytest.mark.fluids
@pytest.mark.seasons
def test_board_moisture_query_unpopulated_layer(mock_board):
    """
    Verify querying moisture on a layer without an active field returns 0.0.
    """
    assert mock_board.moisture("unpopulated-layer", 50, 50) == 0.0