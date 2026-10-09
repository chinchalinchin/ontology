import argparse
import os
import sys
import yaml
from models import SoundsRoot, ScoreRoot, CompiledScoreDTO, ScoreMetadataDTO, NoteEventDTO
from loader import FAMOUS_SCORES, parse_music21_score
import sound


def load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compile_yaml_score(score_entry, sounds_config, score_name: str) -> CompiledScoreDTO:
    note_map = {n.name: n.frequency for n in sounds_config.sounds.notes}
    beat_map = {b.name: b.value for b in sounds_config.sounds.beats}

    quarter_duration = 60.0 / score_entry.bpm
    whole_duration = quarter_duration * 4.0
    events: list[NoteEventDTO] = []

    if score_entry.tracks:
        for _, track_notes in score_entry.tracks.items():
            track_time = 0.0
            for item in track_notes:
                dur = beat_map[item.beat] * whole_duration
                for n_name in item.notes:
                    events.append(
                        NoteEventDTO(
                            start_time=track_time,
                            frequency=note_map[n_name],
                            duration=dur,
                            pitch_name=n_name,
                        )
                    )
                track_time += dur
    else:
        curr_time = 0.0
        for item in score_entry.notes:
            dur = beat_map[item.beat] * whole_duration
            for n_name in item.notes:
                events.append(
                    NoteEventDTO(
                        start_time=curr_time,
                        frequency=note_map[n_name],
                        duration=dur,
                        pitch_name=n_name,
                    )
                )
            curr_time += dur

    events.sort(key=lambda e: e.start_time)
    metadata = ScoreMetadataDTO(title=score_name, bpm=score_entry.bpm, time_signature=score_entry.signature)
    return CompiledScoreDTO(metadata=metadata, events=events)


def main():
    parser = argparse.ArgumentParser(description="SDL2 Procedural Audio Synthesizer & Music21 Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ------------------------------------------------------------------------
    # Subcommand: yaml
    # ------------------------------------------------------------------------
    yaml_parser = subparsers.add_parser("yaml", help="Synthesize from a local declarative YAML score")
    yaml_parser.add_argument("--score", default="score.yaml", help="Path to score.yaml")
    yaml_parser.add_argument("--sounds", default="sounds.yaml", help="Path to sounds.yaml")

    # ------------------------------------------------------------------------
    # Subcommand: corpus
    # ------------------------------------------------------------------------
    corpus_parser = subparsers.add_parser("corpus", help="Load and synthesize scores via music21")
    corpus_parser.add_argument("--name", choices=list(FAMOUS_SCORES.keys()), help="Name of famous piano score")
    corpus_parser.add_argument("--list", action="store_true", help="List available scores in the lookup catalog")
    corpus_parser.add_argument("--bpm", type=float, help="Override playback tempo (BPM)")
    corpus_parser.add_argument("--max-measures", type=int, help="Limit number of measures to process")

    # ------------------------------------------------------------------------
    # Subcommand: url
    # ------------------------------------------------------------------------
    url_parser = subparsers.add_parser("url", help="Fetch and synthesize an unauthenticated public-domain score URL")
    url_parser.add_argument("score_url", help="URL to MusicXML (.mxl, .xml) or Humdrum (.krn)")
    url_parser.add_argument("--bpm", type=float, help="Override playback tempo (BPM)")
    url_parser.add_argument("--max-measures", type=int, help="Limit number of measures to process")

    args = parser.parse_args()

    # Route: YAML
    if args.command == "yaml":
        sounds = SoundsRoot.model_validate(load_yaml(args.sounds))
        scores = ScoreRoot.model_validate(load_yaml(args.score))

        for score_name, score_entry in scores.score.items():
            print(f"Loading '{score_name}' from YAML at {score_entry.bpm} BPM...")
            compiled = compile_yaml_score(score_entry, sounds, score_name)
            sound.play(compiled.to_event_tuples())

    # Route: Corpus Catalog
    elif args.command == "corpus":
        if args.list:
            print("\nAvailable Piano Works in Lookup Catalog:")
            for key, info in FAMOUS_SCORES.items():
                source_type = "Built-in music21 Corpus" if info["is_corpus"] else "KernScores Public Domain URL"
                print(f"  * {key:28} | {info['composer']} - {info['title']} ({source_type})")
            sys.exit(0)

        if not args.name:
            corpus_parser.error("--name is required unless --list is passed.")

        cfg = FAMOUS_SCORES[args.name]
        cfg = FAMOUS_SCORES[args.name]
        print(f"Ingesting '{cfg['title']}' by {cfg['composer']}...")
        compiled = parse_music21_score(
            source=cfg["source"],
            is_corpus=cfg["is_corpus"],
            score_format=cfg.get("format"),
            override_bpm=args.bpm or cfg["default_bpm"],
            max_measures=args.max_measures,
            title=cfg["title"],
            composer=cfg["composer"],
        )
        print(f"Synthesizing {len(compiled.events)} events at {compiled.metadata.bpm} BPM...")
        sound.play(compiled.to_event_tuples())

    # Route: External URL
    elif args.command == "url":
        print(f"Fetching remote score from: {args.score_url}...")
        compiled = parse_music21_score(
            source=args.score_url,
            is_corpus=False,
            override_bpm=args.bpm,
            max_measures=args.max_measures,
        )
        print(f"Synthesizing {len(compiled.events)} events at {compiled.metadata.bpm} BPM...")
        sound.play(compiled.to_event_tuples())


if __name__ == "__main__":
    main()