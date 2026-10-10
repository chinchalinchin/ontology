"""Music21 corpus parser and metadata extraction module."""

import logging
from typing import Dict, List, Optional, Union

from music21 import chord, converter, corpus, meter, note, tempo
from models import CompiledScoreDTO, NoteEventDTO, ScoreMetadataDTO
import files

logger = logging.getLogger(__name__)

DEFAULT_PIANO_HARMONICS = [1.0, 0.35, 0.10, 0.02]
DEFAULT_PIANO_ATTACK = 0.005
DEFAULT_PIANO_DECAY = 2.2

FAMOUS_SCORES: Dict[str, dict] = {
    # --- CHOPIN ---
    "chopin_mazurka_op6_no2": {
        "title": "Mazurka in C-sharp minor, Op. 6 No. 2",
        "composer": "Frédéric Chopin",
        "source": "chopin/mazurka06-2.krn",
        "format": "humdrum",
        "default_bpm": 132.0,
        "is_corpus": True,
    },
    # --- BEETHOVEN ---
    "beethoven_quartet_op18_no1_mvt1": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 1 - Allegro)",
        "composer": "Ludwig van Beethoven",
        "source": "beethoven/opus18no1/movement1.krn",
        "format": "humdrum",
        "default_bpm": 120.0,
        "is_corpus": True,
    },
    "beethoven_quartet_op18_no1_mvt2": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 2 - Adagio)",
        "composer": "Ludwig van Beethoven",
        "source": "beethoven/opus18no1/movement2.krn",
        "format": "humdrum",
        "default_bpm": 56.0,
        "is_corpus": True,
    },
    "beethoven_quartet_op18_no1_mvt3": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 3 - Scherzo)",
        "composer": "Ludwig van Beethoven",
        "source": "beethoven/opus18no1/movement3.krn",
        "format": "humdrum",
        "default_bpm": 138.0,
        "is_corpus": True,
    },
    "beethoven_quartet_op18_no1_mvt4": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 4 - Allegro)",
        "composer": "Ludwig van Beethoven",
        "source": "beethoven/opus18no1/movement4.krn",
        "format": "humdrum",
        "default_bpm": 144.0,
        "is_corpus": True,
    },
    "beethoven_grosse_fuge_op133": {
        "title": "Große Fuge in B-flat major, Op. 133",
        "composer": "Ludwig van Beethoven",
        "source": "beethoven/opus133.mxl",
        "format": "musicxml",
        "default_bpm": 112.0,
        "is_corpus": True,
    },
    # --- BACH ---
    "bach_chorale_bwv66_6": {
        "title": "Chorale BWV 66.6 ('Christ lag in Todesbanden')",
        "composer": "Johann Sebastian Bach",
        "source": "bach/bwv66.6",
        "format": "humdrum",
        "default_bpm": 72.0,
        "is_corpus": True,
    },
    "bach_chorale_bwv269": {
        "title": "Chorale BWV 269 ('Aus meines Herzens Grunde')",
        "composer": "Johann Sebastian Bach",
        "source": "bach/bwv269.mxl",
        "format": "musicxml",
        "default_bpm": 80.0,
        "is_corpus": True,
    },
    "bach_chorale_bwv1_6": {
        "title": "Chorale BWV 1.6 ('Wie schön leuchtet der Morgenstern')",
        "composer": "Johann Sebastian Bach",
        "source": "bach/bwv1.6.mxl",
        "format": "musicxml",
        "default_bpm": 84.0,
        "is_corpus": True,
    },
    "bach_chorale_bwv10_7": {
        "title": "Chorale BWV 10.7 ('Meine Seel erhebt den Herren')",
        "composer": "Johann Sebastian Bach",
        "source": "bach/bwv10.7.mxl",
        "format": "musicxml",
        "default_bpm": 76.0,
        "is_corpus": True,
    },
}


def detect(source: str) -> Optional[str]:
    """Infer file or score representation format from extension or name."""
    lowered = source.lower()
    if ".krn" in lowered or "humdrum" in lowered:
        return "humdrum"
    if ".mxl" in lowered or ".xml" in lowered or "musicxml" in lowered:
        return "musicxml"
    if ".abc" in lowered:
        return "abc"
    if ".mid" in lowered or ".midi" in lowered:
        return "midi"
    return None


def resolve(source: str) -> str:
    """Resolve file system path for non-corpus score sources."""
    return str(files.resolve(source))


def parse(
    source: Union[str, List[str]],
    is_corpus: bool = False,
    score_format: Optional[str] = None,
    override_bpm: Optional[float] = None,
    max_measures: Optional[int] = None,
    title: Optional[str] = None,
    composer: Optional[str] = None,
) -> CompiledScoreDTO:
    """Ingest and compile a music21 score stream into NoteEventDTO representations."""
    first_src = source if isinstance(source, str) else source[0]
    fmt = score_format or detect(first_src)

    if is_corpus:
        logger.info("Parsing corpus score: %s", first_src)
        score_stream = corpus.parse(first_src)
    else:
        resolved_path = resolve(first_src)
        logger.info("Parsing local score file: %s (format=%s)", resolved_path, fmt)
        score_stream = converter.parse(resolved_path, format=fmt)

    if max_measures is not None and max_measures > 0:
        logger.debug("Restricting score to %d measures", max_measures)
        score_stream = score_stream.measures(None, max_measures)

    try:
        score_stream = score_stream.stripTies()
    except Exception as exc:
        logger.debug("Failed to strip ties: %s", exc)

    detected_bpm = None
    tempo_marks = score_stream.recurse().getElementsByClass(tempo.MetronomeMark)
    if tempo_marks:
        try:
            detected_bpm = float(tempo_marks[0].getQuarterBPM())
        except Exception as exc:
            logger.debug("Could not determine tempo mark BPM: %s", exc)

    effective_bpm = override_bpm or detected_bpm or 120.0
    seconds_per_quarter = 60.0 / effective_bpm

    time_sig_str = None
    time_sigs = score_stream.recurse().getElementsByClass(meter.TimeSignature)
    if time_sigs:
        try:
            time_sig_str = f"{time_sigs[0].numerator}/{time_sigs[0].denominator}"
        except Exception as exc:
            logger.debug("Could not parse time signature: %s", exc)

    resolved_title = title or (score_stream.metadata.title if score_stream.metadata else "Untitled")
    resolved_composer = composer or (score_stream.metadata.composer if score_stream.metadata else "Unknown")

    events: List[NoteEventDTO] = []
    parts = score_stream.parts if len(score_stream.parts) > 0 else [score_stream]

    for part in parts:
        flat_notes = part.flatten().notes if hasattr(part, "flatten") else part.flat.notes
        for el in flat_notes:
            start_sec = float(el.offset) * seconds_per_quarter
            dur_sec = float(el.quarterLength) * seconds_per_quarter

            if dur_sec <= 0.0:
                dur_sec = 0.02

            vel = 0.75
            if el.volume is not None and el.volume.velocityScalar is not None:
                vel = max(0.05, min(1.0, float(el.volume.velocityScalar)))

            if isinstance(el, note.Note):
                events.append(
                    NoteEventDTO(
                        start_time=start_sec,
                        frequency=float(el.pitch.frequency),
                        duration=dur_sec,
                        pitch_name=el.pitch.nameWithOctave,
                        velocity=vel,
                        attack=DEFAULT_PIANO_ATTACK,
                        decay=DEFAULT_PIANO_DECAY,
                        harmonics=DEFAULT_PIANO_HARMONICS,
                    )
                )
            elif isinstance(el, chord.Chord):
                for p in el.pitches:
                    events.append(
                        NoteEventDTO(
                            start_time=start_sec,
                            frequency=float(p.frequency),
                            duration=dur_sec,
                            pitch_name=p.nameWithOctave,
                            velocity=vel,
                            attack=DEFAULT_PIANO_ATTACK,
                            decay=DEFAULT_PIANO_DECAY,
                            harmonics=DEFAULT_PIANO_HARMONICS,
                        )
                    )

    events.sort(key=lambda e: e.start_time)
    logger.info("Extracted %d note events from score '%s'", len(events), resolved_title)

    metadata = ScoreMetadataDTO(
        title=resolved_title,
        composer=resolved_composer,
        bpm=effective_bpm,
        time_signature=time_sig_str,
    )
    return CompiledScoreDTO(metadata=metadata, events=events)