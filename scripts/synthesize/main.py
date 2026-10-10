"""CLI entry point for procedural synthesis and music21 score ingestion."""

import argparse
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import compile
import files
import loader
import sound

logger = logging.getLogger("synthesize")
SCRIPT_DIR = Path(__file__).resolve().parent


def render_catalog() -> str:
    """Render the music catalog markdown output via Jinja2."""
    template_dir = SCRIPT_DIR / "templates"
    jinja_env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = jinja_env.get_template("list.md.j2")
    return template.render(scores=loader.FAMOUS_SCORES)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="SDL2 Procedural Audio Synthesizer & Music21 Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: synthesize
    yaml_parser = subparsers.add_parser("synthesize", help="Synthesize from a local declarative YAML score")
    yaml_parser.add_argument("--score", default="score.yaml", help="Path to score.yaml")
    yaml_parser.add_argument("--sounds", default="sounds.yaml", help="Path to sounds.yaml")

    # Subcommand: ingest
    corpus_parser = subparsers.add_parser("ingest", help="Load and synthesize scores via music21")
    corpus_parser.add_argument("--name", choices=list(loader.FAMOUS_SCORES.keys()), help="Name of famous piano score")
    corpus_parser.add_argument("--list", action="store_true", help="List available scores in the lookup catalog")
    corpus_parser.add_argument("--bpm", type=float, help="Override playback tempo (BPM)")
    corpus_parser.add_argument("--max-measures", type=int, help="Limit number of measures to process")

    args = parser.parse_args()

    if args.command == "synthesize":
        sounds = files.load_sounds(args.sounds)
        scores = files.load_score(args.score)

        for score_name, score_entry in scores.score.items():
            logger.info("Processing score '%s' at %.2f BPM", score_name, score_entry.bpm)
            compiled = compile.score(score_entry, sounds, score_name)
            sound.play(compiled.to_event_tuples())

    elif args.command == "ingest":
        if args.list:
            rendered_catalog = render_catalog()
            logger.info("\n%s", rendered_catalog)
            return

        if not args.name:
            corpus_parser.error("--name is required unless --list is passed.")

        entry = loader.FAMOUS_SCORES[args.name]
        logger.info("Ingesting '%s' by %s...", entry["title"], entry["composer"])

        compiled = loader.parse(
            source=entry["source"],
            is_corpus=entry["is_corpus"],
            score_format=entry.get("format"),
            override_bpm=args.bpm or entry["default_bpm"],
            max_measures=args.max_measures,
            title=entry["title"],
            composer=entry["composer"],
        )
        logger.info("Synthesizing %d events at %.2f BPM...", len(compiled.events), compiled.metadata.bpm)
        sound.play(compiled.to_event_tuples())


if __name__ == "__main__":
    main()