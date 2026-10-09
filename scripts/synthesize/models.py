from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


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


class ScoreNote(BaseModel):
    # Accepts either note: "A4" or notes: ["A2", "E3", "C4", "A4"]
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
    notes: List[ScoreNote]


class ScoreRoot(BaseModel):
    score: Dict[str, ScoreEntry]