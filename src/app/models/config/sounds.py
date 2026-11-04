"""
@domain.model
@app.config
@modality.action

# Ontology: Source - app.models.config.actions

Action Configuration Models.
"""
# Standard Libraries
from typing import Dict
from dataclasses import dataclass

# Application Libraries
from app.models.config import Configuration

class Sound:
    pass

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class SoundConfiguration(Configuration):
    id: str
    data: Dict[str, Sound]