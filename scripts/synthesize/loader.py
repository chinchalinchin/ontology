import hashlib
import os
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Union

from music21 import chord, converter, corpus, meter, note, tempo
from models import CompiledScoreDTO, NoteEventDTO, ScoreMetadataDTO


FAMOUS_SCORES: Dict[str, dict] = {
    # --- CHOPIN ---
    "chopin_mazurka_op6_no2": {
        "title": "Mazurka in C-sharp minor, Op. 6 No. 2",
        "composer": "Frédéric Chopin",
        "sources": ["chopin/mazurka06-2.krn"],
        "format": "humdrum",
        "default_bpm": 132.0,
        "is_corpus": True,
    },
    # --- BEETHOVEN ---
    "beethoven_quartet_op18_no1_mvt1": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 1 - Allegro)",
        "composer": "Ludwig van Beethoven",
        "sources": ["beethoven/opus18no1/movement1.krn"],
        "format": "humdrum",
        "default_bpm": 120.0,
        "is_corpus": True,
    },
    "beethoven_quartet_op18_no1_mvt2": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 2 - Adagio)",
        "composer": "Ludwig van Beethoven",
        "sources": ["beethoven/opus18no1/movement2.krn"],
        "format": "humdrum",
        "default_bpm": 56.0,
        "is_corpus": True,
    },
    "beethoven_quartet_op18_no1_mvt3": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 3 - Scherzo)",
        "composer": "Ludwig van Beethoven",
        "sources": ["beethoven/opus18no1/movement3.krn"],
        "format": "humdrum",
        "default_bpm": 138.0,
        "is_corpus": True,
    },
    "beethoven_quartet_op18_no1_mvt4": {
        "title": "String Quartet No. 1 in F major, Op. 18 No. 1 (Mvt 4 - Allegro)",
        "composer": "Ludwig van Beethoven",
        "sources": ["beethoven/opus18no1/movement4.krn"],
        "format": "humdrum",
        "default_bpm": 144.0,
        "is_corpus": True,
    },
    "beethoven_grosse_fuge_op133": {
        "title": "Große Fuge in B-flat major, Op. 133",
        "composer": "Ludwig van Beethoven",
        "sources": ["beethoven/opus133.mxl"],
        "format": "musicxml",
        "default_bpm": 112.0,
        "is_corpus": True,
    },
    # --- BACH ---
    "bach_chorale_bwv66_6": {
        "title": "Chorale BWV 66.6 ('Christ lag in Todesbanden')",
        "composer": "Johann Sebastian Bach",
        "sources": ["bach/bwv66.6"],
        "format": "humdrum",
        "default_bpm": 72.0,
        "is_corpus": True,
    },
    "bach_chorale_bwv269": {
        "title": "Chorale BWV 269 ('Aus meines Herzens Grunde')",
        "composer": "Johann Sebastian Bach",
        "sources": ["bach/bwv269.mxl"],
        "format": "musicxml",
        "default_bpm": 80.0,
        "is_corpus": True,
    },
    "bach_chorale_bwv1_6": {
        "title": "Chorale BWV 1.6 ('Wie schön leuchtet der Morgenstern')",
        "composer": "Johann Sebastian Bach",
        "sources": ["bach/bwv1.6.mxl"],
        "format": "musicxml",
        "default_bpm": 84.0,
        "is_corpus": True,
    },
    "bach_chorale_bwv10_7": {
        "title": "Chorale BWV 10.7 ('Meine Seel erhebt den Herren')",
        "composer": "Johann Sebastian Bach",
        "sources": ["bach/bwv10.7.mxl"],
        "format": "musicxml",
        "default_bpm": 76.0,
        "is_corpus": True,
    },
}


def detect_format(source: str) -> Optional[str]:
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


def resolve_and_cache(sources: Union[str, List[str]], fmt: Optional[str] = None) -> str:
    """Fetches and caches scores locally, trying fallback mirror URLs on network errors."""
    candidate_urls = [sources] if isinstance(sources, str) else list(sources)

    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "scores")
    os.makedirs(cache_dir, exist_ok=True)

    last_error = None
    for src in candidate_urls:
        if not src.startswith(("http://", "https://")):
            return src

        parsed = urllib.parse.urlsplit(src)
        query_params = urllib.parse.parse_qs(parsed.query)

        if "file" in query_params and query_params["file"]:
            filename = query_params["file"][0]
        else:
            base = os.path.basename(parsed.path)
            if base and "." in base:
                filename = base
            else:
                ext = ".krn" if fmt == "humdrum" else (".mxl" if fmt == "musicxml" else ".txt")
                url_hash = hashlib.md5(src.encode("utf-8")).hexdigest()[:10]
                filename = f"score_{url_hash}{ext}"

        cached_path = os.path.join(cache_dir, filename)
        if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
            return cached_path

        try:
            req = urllib.request.Request(
                src,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"},
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read()

            if content:
                with open(cached_path, "wb") as f:
                    f.write(content)
                return cached_path
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise RuntimeError(f"Could not resolve or fetch score from: {sources}")


def parse_music21_score(
    source: Union[str, List[str]],
    is_corpus: bool = False,
    score_format: Optional[str] = None,
    override_bpm: Optional[float] = None,
    max_measures: Optional[int] = None,
    title: Optional[str] = None,
    composer: Optional[str] = None,
) -> CompiledScoreDTO:
    first_src = source if isinstance(source, str) else source[0]
    fmt = score_format or detect_format(first_src)

    if is_corpus:
        score_stream = corpus.parse(first_src)
    else:
        resolved_path = resolve_and_cache(source, fmt)
        score_stream = converter.parse(resolved_path, format=fmt)

    if max_measures is not None and max_measures > 0:
        score_stream = score_stream.measures(None, max_measures)

    try:
        score_stream = score_stream.stripTies()
    except Exception:
        pass

    # Extract tempo
    detected_bpm = None
    tempo_marks = score_stream.recurse().getElementsByClass(tempo.MetronomeMark)
    if tempo_marks:
        try:
            detected_bpm = float(tempo_marks[0].getQuarterBPM())
        except Exception:
            pass

    effective_bpm = override_bpm or detected_bpm or 120.0
    seconds_per_quarter = 60.0 / effective_bpm

    # Extract time signature
    time_sig_str = None
    time_sigs = score_stream.recurse().getElementsByClass(meter.TimeSignature)
    if time_sigs:
        try:
            time_sig_str = f"{time_sigs[0].numerator}/{time_sigs[0].denominator}"
        except Exception:
            pass

    resolved_title = title or (score_stream.metadata.title if score_stream.metadata else "Untitled")
    resolved_composer = composer or (score_stream.metadata.composer if score_stream.metadata else "Unknown")

    events: List[NoteEventDTO] = []
    parts = score_stream.parts if len(score_stream.parts) > 0 else [score_stream]

    for part in parts:
        flat_notes = part.flatten().notes if hasattr(part, "flatten") else part.flat.notes
        for el in flat_notes:
            start_sec = float(el.offset) * seconds_per_quarter
            dur_sec = float(el.quarterLength) * seconds_per_quarter

            # Clamp unmetered grace notes to a minimal audible duration
            if dur_sec <= 0.0:
                dur_sec = 0.02

            vel = 1.0
            if el.volume is not None and el.volume.velocityScalar is not None:
                vel = float(el.volume.velocityScalar)

            if isinstance(el, note.Note):
                events.append(
                    NoteEventDTO(
                        start_time=start_sec,
                        frequency=float(el.pitch.frequency),
                        duration=dur_sec,
                        pitch_name=el.pitch.nameWithOctave,
                        velocity=vel,
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
                        )
                    )

    events.sort(key=lambda e: e.start_time)

    metadata = ScoreMetadataDTO(
        title=resolved_title,
        composer=resolved_composer,
        bpm=effective_bpm,
        time_signature=time_sig_str,
    )
    return CompiledScoreDTO(metadata=metadata, events=events)