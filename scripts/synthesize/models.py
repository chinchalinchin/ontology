from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, model_validator


# ============================================================================
# Declarative Sound & Hardware Schema
# ============================================================================

class SignatureModel(BaseModel):
    name: str
    beats_per_measure: int = Field(gt=0)
    beat_unit: int = Field(gt=0)


class BeatModel(BaseModel):
    name: str
    value: float = Field(gt=0.0)


class NoteFrequencyModel(BaseModel):
    name: str
    frequency: float = Field(ge=0.0)


class SoundConfig(BaseModel):
    signatures: List[SignatureModel]
    beats: List[BeatModel]
    notes: List[NoteFrequencyModel]


class SoundsRoot(BaseModel):
    sounds: SoundConfig


# ============================================================================
# Declarative YAML Score Schema
# ============================================================================

class ScoreNote(BaseModel):
    note: Optional[Union[str, List[str]]] = None
    notes: Optional[List[str]] = None
    beat: str

    @model_validator(mode="after")
    def normalize_chord(self):
        target = self.notes if self.notes is not None else self.note
        if target is None:
            raise ValueError("Each note item must specify 'note' or 'notes'")
        if isinstance(target, str):
            self.notes = [target]
        else:
            self.notes = list(target)
        return self


class ScoreEntry(BaseModel):
    signature: str
    bpm: float = Field(default=120.0, gt=0.0)
    notes: Optional[List[ScoreNote]] = None
    tracks: Optional[Dict[str, List[ScoreNote]]] = None

    @model_validator(mode="after")
    def validate_content(self):
        if not self.notes and not self.tracks:
            raise ValueError("Score must specify either 'notes' or 'tracks'")
        return self


class ScoreRoot(BaseModel):
    score: Dict[str, ScoreEntry]


# ============================================================================
# Ingestion DTOs (music21 & Synthesizer Interface)
# ============================================================================

class NoteEventDTO(BaseModel):
    """Atomic time-domain sound event consumed by the Cython playback engine."""
    start_time: float = Field(ge=0.0, description="Start offset in seconds")
    frequency: float = Field(ge=0.0, description="Fundamental frequency in Hz (0.0 = rest)")
    duration: float = Field(gt=0.0, description="Sounding duration in seconds")
    pitch_name: Optional[str] = Field(default=None, description="Scientific pitch name (e.g. C#4)")
    velocity: float = Field(default=1.0, ge=0.0, le=1.0, description="Normalized velocity scalar")


class ScoreMetadataDTO(BaseModel):
    title: str
    composer: Optional[str] = None
    bpm: float = Field(gt=0.0)
    time_signature: Optional[str] = None


class CompiledScoreDTO(BaseModel):
    """Aggregated timeline container ready for playback or serialization."""
    metadata: ScoreMetadataDTO
    events: List[NoteEventDTO]

    def to_event_tuples(self) -> List[Tuple[float, float, float]]:
        """Converts events to (start_time, frequency, duration) tuples for test.pyx."""
        return [(e.start_time, e.frequency, e.duration) for e in self.events]