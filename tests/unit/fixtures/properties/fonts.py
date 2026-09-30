"""
# Ontology: tests.unit.fixtures.properties.fonts

Mock Font Property fixtures.
"""
# External Libraries
import pytest

# Application Libraries
from app.models.properties import (
    RGBA,
    Outline,
    FontProperties,
)

# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK PROPERTIES
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_font_properties() -> FontProperties:
    """FontProperties dataclass fixture for typography testing."""
    return FontProperties(
        size=24,
        alignment="left",
        color=RGBA(
            r=255,
            g=255, 
            b=255, 
            a=255
        ),
        outline=Outline(
            color=RGBA(
                r=0, 
                g=0, 
                b=0, 
                a=255
            ), 
            width=2
        ),
        bold=True,
        italics=False,
        underline=False,
        strikethrough=False,
        margins=0.05
    )