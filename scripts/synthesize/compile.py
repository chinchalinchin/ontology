"""Time-domain score compilation engine."""

import logging
from typing import Dict, List, Optional

from models import (
    CompiledScoreDTO,
    NoteEventDTO,
    ScoreEntry,
    ScoreMetadataDTO,
    ScoreNote,
    SoundsRoot,
    TimbreModel,
    TrackEntry,
)

logger = logging.getLogger(__name__)

DEFAULT_DYNAMIC_SCALAR = 0.75  # Equivalent to 'mf'
DEFAULT_TIMBRE = TimbreModel(harmonics=[1.0, 0.35, 0.10, 0.02], attack=0.005, decay=2.2)


def _resolve_velocity(
    note_dyn: Optional[str],
    track_dyn: Optional[str],
    dynamics_map: Dict[str, float],
) -> float:
    selected = note_dyn or track_dyn
    if selected and selected in dynamics_map:
        return dynamics_map[selected]
    return DEFAULT_DYNAMIC_SCALAR


def _resolve_timbre(
    note_timbre: Optional[str],
    track_timbre: Optional[str],
    timbres_map: Dict[str, TimbreModel],
) -> TimbreModel:
    selected = note_timbre or track_timbre
    if selected and selected in timbres_map:
        return timbres_map[selected]
    return DEFAULT_TIMBRE


def score(score_entry: ScoreEntry, sounds_config: SoundsRoot, score_name: str) -> CompiledScoreDTO:
    """Compile a declarative YAML score entry into a chronological CompiledScoreDTO."""
    logger.info("Compiling score '%s' at %.2f BPM", score_name, score_entry.bpm)

    note_map = {n.name: n.frequency for n in sounds_config.sounds.notes}
    beat_map = {b.name: b.value for b in sounds_config.sounds.beats}
    dynamics_map = sounds_config.sounds.dynamics
    timbres_map = sounds_config.sounds.timbres

    quarter_duration = 60.0 / score_entry.bpm
    whole_duration = quarter_duration * 4.0
    events: List[NoteEventDTO] = []

    if score_entry.tracks:
        for track_name, track_content in score_entry.tracks.items():
            if isinstance(track_content, TrackEntry):
                track_timbre_name = track_content.timbre
                track_default_dyn = track_content.default_dynamic
                items = track_content.notes
            else:
                track_timbre_name = None
                track_default_dyn = None
                items = track_content

            logger.debug(
                "Compiling track '%s' (timbre: %s, dynamic: %s)",
                track_name,
                track_timbre_name,
                track_default_dyn,
            )
            track_time = 0.0
            for item in items:
                dur = beat_map[item.beat] * whole_duration
                vel = _resolve_velocity(item.dynamic, track_default_dyn, dynamics_map)
                timbre_cfg = _resolve_timbre(item.timbre, track_timbre_name, timbres_map)

                for n_name in item.notes:
                    events.append(
                        NoteEventDTO(
                            start_time=track_time,
                            frequency=note_map[n_name],
                            duration=dur,
                            pitch_name=n_name,
                            velocity=vel,
                            attack=timbre_cfg.attack,
                            decay=timbre_cfg.decay,
                            harmonics=timbre_cfg.harmonics,
                        )
                    )
                track_time += dur
    else:
        curr_time = 0.0
        for item in (score_entry.notes or []):
            dur = beat_map[item.beat] * whole_duration
            vel = _resolve_velocity(item.dynamic, None, dynamics_map)
            timbre_cfg = _resolve_timbre(item.timbre, None, timbres_map)

            for n_name in item.notes:
                events.append(
                    NoteEventDTO(
                        start_time=curr_time,
                        frequency=note_map[n_name],
                        duration=dur,
                        pitch_name=n_name,
                        velocity=vel,
                        attack=timbre_cfg.attack,
                        decay=timbre_cfg.decay,
                        harmonics=timbre_cfg.harmonics,
                    )
                )
            curr_time += dur

    events.sort(key=lambda e: e.start_time)
    logger.info("Compiled %d time-domain events for '%s'", len(events), score_name)

    metadata = ScoreMetadataDTO(
        title=score_name,
        bpm=score_entry.bpm,
        time_signature=score_entry.signature,
    )
    return CompiledScoreDTO(metadata=metadata, events=events)