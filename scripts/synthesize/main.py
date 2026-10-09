import argparse
import os
import yaml
from models import SoundsRoot, ScoreRoot
import sound


def load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    cwd = os.getcwd()
    default_score = os.path.join(cwd, "score.yaml")
    default_sounds = os.path.join(cwd, "sounds.yaml")

    parser = argparse.ArgumentParser(description="SDL2 Procedural Piano Audio Synthesizer")
    parser.add_argument("--score", default=default_score, help="Path to score YAML file")
    parser.add_argument("--sounds", default=default_sounds, help="Path to sounds YAML file")
    args = parser.parse_args()

    sounds_validated = SoundsRoot.model_validate(load_yaml(args.sounds))
    note_map = {n.name: n.frequency for n in sounds_validated.sounds.notes}
    beat_map = {b.name: b.value for b in sounds_validated.sounds.beats}

    score_validated = ScoreRoot.model_validate(load_yaml(args.score))

    for score_name, score_entry in score_validated.score.items():
        print(f"Synthesizing polyphonic score '{score_name}' at {score_entry.bpm} BPM...")
        quarter_duration = 60.0 / score_entry.bpm
        whole_duration = quarter_duration * 4.0

        resolved_chords = []
        for item in score_entry.notes:
            freqs = []
            for n_name in item.notes:
                if n_name not in note_map:
                    raise ValueError(f"Note '{n_name}' not declared in {args.sounds}")
                freqs.append(note_map[n_name])

            duration = beat_map[item.beat] * whole_duration
            resolved_chords.append((freqs, duration))

        sound.play(resolved_chords)


if __name__ == "__main__":
    main()