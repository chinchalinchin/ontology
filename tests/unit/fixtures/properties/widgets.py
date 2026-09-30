"""
# Ontology: tests.unit.fixtures.properties.widgets

Mock Widget Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    WidgetProperties,
    WidgetPropertyInstances,
)

# Cython Libraries
from libs.core.models import (
    Dimensions, 

)

@pytest.fixture
def mock_widget_properties() -> WidgetPropertyInstances:
    """
    Standard widget properties fixture providing prototype dimensions for
    slot buttons and transparent slot overlay panes.
    """
    return WidgetPropertyInstances(
        icons = {
            "test-icon": WidgetProperties(
                dimensions=Dimensions(w=16, l=16), 
                frames=["sword"]
            ),
            "weapons": WidgetProperties(
                dimensions=Dimensions(w=32, l=32), 
                frames=["shortsword", "dagger"]
            )
        },
        panes={
            "test-pane": WidgetProperties(
                dimensions=Dimensions(w=200, l=200)
            ),
            "transparent-slot": WidgetProperties(
                dimensions=Dimensions(w=40, l=40)
            ),
            "neutral": WidgetProperties(
                dimensions=Dimensions(w=318, l=180)
            )
        },
        pages = {
            "test-page": WidgetProperties(
                dimensions=Dimensions(w=100, l=100) 
            )
        },
        buttons={
            "test-btn": WidgetProperties(
                dimensions=Dimensions(w=32, l=32)
            ),
            "slot": WidgetProperties(
                dimensions=Dimensions(w=40, l=40)
            ),
            "arrow-up": WidgetProperties(
                dimensions=Dimensions(w=24, l=24)
            ),
            "arrow-down": WidgetProperties(
                dimensions=Dimensions(w=24, l=24)
            )
        },
        meters = {
            "test-meter": WidgetProperties(
                dimensions=Dimensions(w=50, l=10)
            )
        }
    )