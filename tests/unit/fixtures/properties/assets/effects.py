"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.effects

# Ontology: Tests - tests.unit.fixtures.properties.effects

Mock Effect Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.static.semantics import Frequencies
from app.models.properties import (
    Frequency,
    EffectProperties,
    EffectPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
    Hitbox,
)


@pytest.fixture
def mock_effect_properties() -> EffectPropertyInstances:
    return EffectPropertyInstances(
        collectables={
            "coin": EffectProperties(
                count=8,
                dimensions=Dimensions(w=32, l=32),
                frequency=Frequency(type=Frequencies.CONTINUOUS.value),
                hitboxes=None,
                mass=-1,
            ),
        },
        fluids={
            "waterflow": EffectProperties(
                dimensions=Dimensions(w=96, l=32),
                frequency=Frequency(
                    type=Frequencies.CONTINUOUS.value,
                    delay=20,
                ),
                count=5,
                hitboxes=None,
                priority=-3,
                mass=-1,
            ),
        },
        hazards={
            "lava": EffectProperties(
                count=45,
                dimensions=Dimensions(w=16, l=16),
                frequency=Frequency(type=Frequencies.CONTINUOUS.value),
                hitboxes=None,
                mass=-1,
            ),
            "spike": EffectProperties(
                count=7,
                dimensions=Dimensions(w=64, l=64),
                frequency=Frequency(
                    type=Frequencies.PERIODIC.value,
                    frequency=120,
                ),
                hitboxes=None,
                mass=-1,
            ),
            "bang": EffectProperties(
                count=10,
                dimensions=Dimensions(w=32, l=32),
                frequency=Frequency(type=Frequencies.TEMPORARY.value),
                hitboxes=None,
                mass=-1,
            ),
            "bomb": EffectProperties(
                count=13,
                dimensions=Dimensions(w=32, l=32),
                frequency=Frequency(type=Frequencies.TEMPORARY.value),
                hitboxes=None,
                mass=-1,
            ),
        },
        passive={
            "birdbath": EffectProperties(
                count=5,
                dimensions=Dimensions(w=32, l=64),
                frequency=Frequency(
                    type=Frequencies.PERIODIC.value,
                    frequency=1200,
                ),
                hitboxes=None,
                mass=-1,
            ),
            "grandfather-clock": EffectProperties(
                count=12,
                dimensions=Dimensions(w=32, l=96),
                frequency=Frequency(
                    type=Frequencies.CONTINUOUS.value,
                    delay=60,
                ),
                hitboxes=None,
                mass=0,
            ),
            "torch": EffectProperties(
                count=9,
                dimensions=Dimensions(w=32, l=64),
                frequency=Frequency(
                    type=Frequencies.CONTINUOUS.value,
                    delay=15,
                ),
                hitboxes=None,
                mass=-1,
                priority=1,
            ),
            "splash": EffectProperties(
                count=3,
                dimensions=Dimensions(w=60, l=12),
                frequency=Frequency(
                    type=Frequencies.TEMPORARY.value,
                    delay=15,
                ),
                hitboxes=None,
                mass=-1,
            ),
        },
        reactables={
            "spinning-dummy": EffectProperties(
                count=8,
                dimensions=Dimensions(w=64, l=64),
                frequency=Frequency(
                    type=Frequencies.TEMPORARY.value,
                    persist=True,
                    delay=5,
                    cooldown=30,
                ),
                hitboxes=[
                    Hitbox(Position(2, 20), Dimensions(14, 14)),
                ],
                mass=0,
            ),
        },
    )