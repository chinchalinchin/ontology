"""
@app.config
@workflow.intentions

# Ontology: app.models.config.core

Action Configuration Models.
"""
# Standard Libraries
from typing import (
    Dict
)
from dataclasses import (
    dataclass, 
)

# Application Libraries
from app.models.config import (
    Configuration
)
from app.models.properties import (
    Action
)

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ActionConfiguration(Configuration):
    id: str
    data: Dict[str, Action]