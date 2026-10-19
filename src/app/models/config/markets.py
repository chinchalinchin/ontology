
"""
# Ontology: app.models.config

Models for typing the Market configuration.
"""

# Standard Libraries
from typing import Dict
from dataclasses import dataclass, field

# Application Libraries
from app.models.config.core import Configuration

# ---------------------------------------------------------

@dataclass(slots=True)
class Cost:
    item: str
    quantity: int

@dataclass(slots=True, frozen=True)
class MarketConfiguration(Configuration):
    materials: Dict[str, Dict[str, float]] = field(default_factory=dict)
    blueprints: Dict[str, Dict[str, float]] = field(default_factory=dict)
