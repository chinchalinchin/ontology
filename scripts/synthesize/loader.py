import hashlib
import os
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Union

from music21 import chord, converter, corpus, meter, note, tempo
from models import CompiledScoreDTO, NoteEventDTO, ScoreMetadataDTO


FAMOUS_SCORES: Dict[str, dict] = {
    "fur_elise": {
        "title": "Bagatelle in A minor, WoO 59 ('Für Elise')",
        "composer": "Ludwig van Beethoven",
        "sources": [
            "http://kern.ccarh.org/cgi-bin/ksdata?file=bagat59.krn&l=beethoven/piano",
            "https://raw.githubusercontent.com/craigsapp/beethoven-piano/master/kern/bagat59.krn",
        ],
        "format": "humdrum",
        "default_bpm": 132.0,
        "is_corpus": False,
    },
    "chopin_nocturne_op9_no2": {
        "title": "Nocturne in E-flat major, Op. 9 No. 2",
        "composer": "Frédéric Chopin",
        "sources": [
            "http://kern.ccarh.org/cgi-bin/ksdata?file=noct0902.krn&l=chopin/nocturnes",
            "https://raw.githubusercontent.com/craigsapp/chopin-nocturnes/master/kern/noct0902.krn",
        ],
        "format": "humdrum",
        "default_bpm": 66.0,
        "is_corpus": False,
    },
    "chopin_fantaisie_impromptu": {
        "title": "Fantaisie-Impromptu in C-sharp minor, Op. 66",
        "composer": "Frédéric Chopin",
        "sources": [
            "http://kern.ccarh.org/cgi-bin/ksdata?file=fant66.krn&l=chopin/various",
            "https://raw.githubusercontent.com/craigsapp/chopin-various/master/kern/fant66.krn",
        ],
        "format": "humdrum",
        "default_bpm": 160.0,
        "is_corpus": False,
    },
    "moonlight_sonata": {
        "title": "Piano Sonata No. 14, Op. 27 No. 2 'Moonlight' (1st Mvt)",
        "composer": "Ludwig van Beethoven",
        "sources": [
            "http://kern.ccarh.org/cgi-bin/ksdata?file=sonata14-1.krn&l=beethoven/sonatas",
            "https://raw.githubusercontent.com/craigsapp/beethoven-piano-sonatas/master/kern/sonata14-1.krn",
        ],
        "format": "humdrum",
        "default_bpm": 54.0,
        "is_corpus": False,
    },
    "maple_leaf_rag": {
        "title": "Maple Leaf Rag",
        "composer": "Scott Joplin",
        "sources": ["joplin/maple_leaf_rag.mxl"],
        "format": "musicxml",
        "default_bpm": 100.0,
        "is_corpus": True,
    },
    "chopin_mazurka_op6_no2": {
        "title": "Mazurka in C-sharp minor, Op. 6 No. 2",
        "composer": "Frédéric Chopin",
        "sources": ["chopin/mazurka06-2.krn"],
        "format": "humdrum",
        "default_bpm": 132.0,
        "is_corpus": True,
    },
    "bach_prelude_c_major": {
        "title": "WTC I: Prelude No. 1 in C Major (BWV 846)",
        "composer": "Johann Sebastian Bach",
        "sources": [
            "http://kern.ccarh.org/cgi-bin/ksdata?file=wtc1p01.krn&l=bach/wtc",
            "https://raw.githubusercontent.com/craigsapp/bach-wtc/master/kern/wtc1p01.krn",
        ],
        "format": "humdrum",
        "default_bpm": 80.0,
        "is_corpus": False,
    },
    "bach_chorale_66_6": {
        "title": "Chorale BWV 66.6",
        "composer": "Johann Sebastian Bach",
        "sources": ["bach/bwv66.6"],
        "format": "humdrum",
        "default_bpm": 72.0,
        "is_corpus": True,
    },
}

# Preserve backward-compatibility for scripts inspecting cfg["source"]
for entry in FAMOUS_SCORES.values():
    entry["source"] = entry["sources"][0]


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