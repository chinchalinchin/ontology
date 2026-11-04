"""
@domain.model
@app.config
@modality.auditory

# Ontology: Source - app.models.config.sounds

Sound Configuration models.
"""
# Standard Libraries
from typing import Dict
from dataclasses import dataclass

# Application Libraries
from app.models.config import Configuration

# ---------------------------------------------------------
@dataclass(slots=True, frozen=True)
class Sound:
    pass

@dataclass(slots=True, frozen=True)
class Score:
    pass

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class SoundConfiguration(Configuration):
    id: str
    data: Dict[str, Sound]