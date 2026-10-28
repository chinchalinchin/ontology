"""
@domain.test
@tests.fixtures
@app.asset
@asset.property
@category.tiles

# Ontology: tests.unit.fixtures.properties.widgets

Mock Widget Property fixtures aligned with src/assets/widgets/main.yaml.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    WidgetProperties,
    WidgetPropertyInstances,
)

# Cython Libraries
from libs.core.models import Dimensions


@pytest.fixture
def mock_widget_properties() -> WidgetPropertyInstances:
    return WidgetPropertyInstances(
        buttons={
            "slot": WidgetProperties(dimensions=Dimensions(w=40, l=40)),
            "icon": WidgetProperties(dimensions=Dimensions(w=71, l=28)),
            "label": WidgetProperties(dimensions=Dimensions(w=142, l=28)),
            "arrow-down": WidgetProperties(dimensions=Dimensions(w=24, l=24)),
            "arrow-left": WidgetProperties(dimensions=Dimensions(w=24, l=24)),
            "arrow-right": WidgetProperties(dimensions=Dimensions(w=24, l=24)),
            "arrow-up": WidgetProperties(dimensions=Dimensions(w=24, l=24)),
        },
        icons={
            "digits": WidgetProperties(
                dimensions=Dimensions(w=12, l=14),
                frames=[
                    "zero",
                    "one",
                    "two",
                    "three",
                    "four",
                    "five",
                    "six",
                    "seven",
                    "eight",
                    "nine",
                ],
            ),
            "weapons": WidgetProperties(
                dimensions=Dimensions(w=32, l=32),
                frames=["shortsword", "dagger", "knife", "spear"],
            ),
            "shields": WidgetProperties(
                dimensions=Dimensions(w=32, l=32),
                frames=["buckler"],
            ),
            "portraits": WidgetProperties(
                dimensions=Dimensions(w=50, l=63),
                frames=[
                    "female-persona-1",
                    "female-persona-2",
                    "female-persona-3",
                    "female-persona-4",
                    "female-persona-5",
                    "female-persona-6",
                    "empress-jasilynn",
                    "female-persona-8",
                    "female-persona-9",
                    "female-persona-10",
                    "female-persona-11",
                    "female-persona-12",
                    "female-persona-13",
                    "male-persona-1",
                    "male-persona-2",
                    "male-persona-3",
                    "male-persona-4",
                    "male-persona-5",
                    "male-persona-6",
                    "male-persona-7",
                    "male-persona-8",
                    "male-persona-9",
                    "male-persona-10",
                    "male-persona-11",
                ],
            ),
        },
        meters={
            "health": WidgetProperties(dimensions=Dimensions(w=72, l=20)),
            "magic": WidgetProperties(dimensions=Dimensions(w=72, l=20)),
        },
        pages={
            "dark-dialogue": WidgetProperties(dimensions=Dimensions(w=640, l=96)),
            "dark-notification": WidgetProperties(dimensions=Dimensions(w=192, l=64)),
            "dark-portrait": WidgetProperties(dimensions=Dimensions(w=58, l=69)),
            "paper-scroll": WidgetProperties(dimensions=Dimensions(w=189, l=192)),
            "paper-header-torn": WidgetProperties(dimensions=Dimensions(w=426, l=163)),
            "paper-header": WidgetProperties(dimensions=Dimensions(w=330, l=54)),
            "paper-area": WidgetProperties(dimensions=Dimensions(w=465, l=273)),
            "paper-weathered": WidgetProperties(dimensions=Dimensions(w=96, l=95)),
            "text-label": WidgetProperties(dimensions=Dimensions(w=142, l=28)),
        },
        panes={
            "dark": WidgetProperties(dimensions=Dimensions(w=318, l=180)),
            "dark-small": WidgetProperties(dimensions=Dimensions(w=318, l=78)),
            "dark-thin": WidgetProperties(dimensions=Dimensions(w=173, l=180)),
            "neutral": WidgetProperties(dimensions=Dimensions(w=318, l=180)),
            "neutral-small": WidgetProperties(dimensions=Dimensions(w=318, l=78)),
            "light": WidgetProperties(dimensions=Dimensions(w=318, l=180)),
            "light-small": WidgetProperties(dimensions=Dimensions(w=318, l=78)),
            "header-pane": WidgetProperties(dimensions=Dimensions(w=160, l=140)),
            "transparent-slot": WidgetProperties(dimensions=Dimensions(w=40, l=40)),
            "transparent-block": WidgetProperties(dimensions=Dimensions(w=80, l=80)),
            "transparent-area": WidgetProperties(dimensions=Dimensions(w=400, l=400)),
            "transparent-label": WidgetProperties(dimensions=Dimensions(w=142, l=28)),
        },
    )