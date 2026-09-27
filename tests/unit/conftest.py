"""
# Ontology: tests.unit.conftest
"""
# Standard Libraries
import sys
from pathlib import Path

# NOTE: Inject the src/ directory into the Python path prior to any local imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

pytest_plugins = [
    "tests.unit.fixtures.assets",
    "tests.unit.fixtures.components",
    "tests.unit.fixtures.configuration",
    "tests.unit.fixtures.menus",
    "tests.unit.fixtures.properties",
    "tests.unit.fixtures.services",
    "tests.unit.fixtures.state",
    "tests.unit.fixtures.structures"
]
