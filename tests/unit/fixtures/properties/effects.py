"""
# Ontology: tests.unit.fixtures.properties.effects

Mock Effect Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Lifecycles,
)
from app.models.properties import (
    Lifecycle,
    EffectProperties,
    EffectPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 
)

@pytest.fixture
def mock_effect_properties() -> EffectPropertyInstances:
    return EffectPropertyInstances(
        fluids = {
            'waterflow-01': EffectProperties(
                dimensions=Dimensions(w=32, l=32),
                count=3,
                mass=-1,
                lifecycle=Lifecycle(
                    type=Lifecycles.CONTINUOUS.value,
                    delay=60, 
                    persist=False
                )
            )
        },
        passive = {
            "splash": EffectProperties(
                dimensions=Dimensions(w=16, l=16), 
                count=3, 
                mass=-1,
                lifecycle=Lifecycle(
                    type=Lifecycles.TEMPORARY.value, 
                    delay=60, 
                    frequency=0, 
                    persist=False
                )
            )
        },
        reactables = {
            'reactable-1': EffectProperties(
                dimensions=Dimensions(w=32, l=32),
                count=3,
                mass=-1,
                lifecycle=Lifecycle(
                    type=Lifecycles.TEMPORARY.value, 
                    delay=60, 
                    frequency=0, 
                    persist=True
                )
            )
        }
    )