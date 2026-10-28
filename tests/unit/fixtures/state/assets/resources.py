"""
# Ontology: tests.unit.fixtures.state.resources

Mock Resource State Fixtures aligned with src/data/state/world-01/resources/.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import (
    PerennialStages,
    AnnualStages,
)
from app.models.state import (
    ResourceStateInstances,
    ResourceState,
)

# Cython Libraries
from libs.core.models import Position


@pytest.fixture
def mock_tree_state() -> ResourceState:
    return ResourceState(
        id="deciduous",
        name="the-mighty-oak",
        layer="0",
        position=Position(x=670, y=15),
        stage=PerennialStages.SAPLING.value,
    )


@pytest.fixture
def mock_crop_state() -> ResourceState:
    return ResourceState(
        id="maize",
        name="imperial-cornfield-00",
        layer="0",
        position=Position(x=48, y=770),
        stage=AnnualStages.SPROUT.value,
    )


@pytest.fixture
def mock_resource_states() -> ResourceStateInstances:
    return ResourceStateInstances(
        crops=[
            ResourceState(
                id="maize",
                name="imperial-cornfield-00",
                layer="0",
                position=Position(x=48, y=770),
                stage=AnnualStages.SPROUT.value,
            ),
            ResourceState(
                id="maize",
                name="imperial-cornfield-01",
                layer="0",
                position=Position(x=80, y=770),
                stage=AnnualStages.SPROUT.value,
            ),
            ResourceState(
                id="maize",
                name="imperial-cornfield-02",
                layer="0",
                position=Position(x=114, y=770),
                stage=AnnualStages.SPROUT.value,
            ),
            ResourceState(
                id="maize",
                name="imperial-cornfield-03",
                layer="0",
                position=Position(x=48, y=834),
                stage=AnnualStages.SPROUT.value,
            ),
            ResourceState(
                id="maize",
                name="imperial-cornfield-04",
                layer="0",
                position=Position(x=80, y=834),
                stage=AnnualStages.SPROUT.value,
            ),
            ResourceState(
                id="maize",
                name="imperial-cornfield-05",
                layer="0",
                position=Position(x=114, y=834),
                stage=AnnualStages.SPROUT.value,
            ),
        ],
        trees=[
            ResourceState(
                id="deciduous",
                name="the-mighty-oak",
                layer="0",
                position=Position(x=670, y=15),
                stage=PerennialStages.SAPLING.value,
            ),
            ResourceState(
                id="deciduous",
                name="the-mighty-oak",
                layer="0",
                position=Position(x=690, y=105),
                stage=PerennialStages.BUSH.value,
            ),
            ResourceState(
                id="deciduous",
                name="the-mighty-oak",
                layer="0",
                position=Position(x=685, y=-50),
                stage=PerennialStages.BUSH.value,
            ),
        ],
    )