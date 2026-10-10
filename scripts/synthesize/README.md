# SDL2 Procedural Audio Synthesizer

Real-time, procedural 88-key piano audio synthesis in Python and Cython using raw SDL2 time-domain audio callbacks (`AUDIO_F32SYS`).

## Architecture & Data Flow

1. **`sounds.yaml`**: Defines standard time signatures, fractional beat values (relative to a whole note), and exact fundamental frequencies for all 88 physical grand piano keys ($A_0$–$C_8$) alongside silence (`REST`).
2. **`models.py`**: Pydantic models verifying strictly typed schema parameters and boundary conditions.
3. **`score.yaml`**: Declarative score definitions mapping sequences of symbolic note keys and beats against a configured tempo (BPM).
4. **`main.py`**: CLI entry point converting musical metadata into concrete `(frequency: float, duration_seconds: float)` tuples.
5. **`sound.pyx`**: Low-level Cython module. Runs without the Python GIL inside `SDL_AudioCallback`, calculating additive harmonic sine waves and exponential decay envelopes per sample.

## Building the Cython Extension

Ensure `libsdl2-dev` is present on the host system:

```bash
python setup.py build_ext --inplace
```

## Running the Synthesizer

Execute with default paths (`./score.yaml` and `./sounds.yaml`):

```bash
python main.py
```

Pass a custom score file:

```bash
python main.py --score /path/to/custom_score.yaml
```

## External Source

### music21 catalogue

```python
from music21 import corpus

# Search local corpus for specific composers
for composer in ["chopin", "beethoven", "bach", "joplin"]:
    results = corpus.search(composer)
    print(f"\n--- {composer.upper()} ({len(results)} works found) ---")
    for r in results[:5]:
        print(f"  {r.sourcePath}")
```