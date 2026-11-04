# Procedural Audio Synthesizer & Score Ingestion Engine

`scripts/synthesize` is a real-time, polyphonic procedural sound synthesis and score ingestion pipeline for the `ontology` engine. It provides two distinct pathways for audio generation:

1. **Declarative YAML Score Compilation**: Translates structured musical notation, multi-track arrangements, and custom timbre configurations into scheduled time-domain events.
2. **Music21 Corpus Ingestion**: Parses symbolic music formats (Humdrum `**kern`, MusicXML, MIDI, ABC) from the `music21` corpus or local disk, extracting pitch, duration, ties, and tempo dynamics into synthesizer events.

Audio rendering is driven by a custom C/Cython extension (`sound.pyx`) linked directly to SDL2 audio streams. It features additive harmonic synthesis, Stevens' power law velocity scaling, dynamic spectral brightness, exponential decay envelopes, and dynamic polyphonic headroom management.

## Prerequisites & System Dependencies

The synthesizer requires Python 3.10+ and native SDL2 development libraries.

### 1. System Libraries (SDL2)

The Cython extension compiles against the SDL2 C headers and dynamic libraries.

* **macOS (Homebrew)**:

```bash
brew install sdl2
```

*(The build script automatically checks Homebrew paths: `/opt/homebrew` for Apple Silicon and `/usr/local` for Intel).*

* **Debian / Ubuntu / Linux Mint**:

```bash
sudo apt-get update
sudo apt-get install libsdl2-dev
```

* **Fedora / RHEL**:
```bash
sudo dnf install SDL2-devel
```

### 2. Python Dependencies

Install the required Python packages into your active virtual environment:

```bash
uv pip install cython pyyaml pydantic jinja2 music21
```

*(Or via standard `pip`)*:

```bash
pip install cython pyyaml pydantic jinja2 music21
```

## Compilation

The audio engine (`sound.pyx`) must be compiled into a native C shared object (`.so` on Linux/macOS or `.pyd` on Windows) before running any synthesis commands.

From within the `scripts/synthesize/` directory:

```bash
python setup.py build_ext --inplace
```

To clean and recompile:

```bash
rm -f sound.c sound.*.so
python setup.py build_ext --inplace
```


## Architectural Overview

```
scripts/synthesize/
├── compile.py          # Time-domain score compiler for declarative YAML
├── files.py            # Path resolution and YAML schema loader
├── loader.py           # Music21 corpus/file parser and format detection
├── main.py             # CLI entry point (synthesize & ingest subcommands)
├── models.py           # Pydantic data schemas and DTO definitions
├── score.yaml          # Declarative score definitions
├── sounds.yaml         # Frequency, beat unit, dynamic, and timbre mappings
├── setup.py            # Cython build script
├── sound.pyx           # Low-level SDL2 audio callback and additive synth engine
└── templates/
    └── list.md.j2      # Jinja2 template for rendering score catalog tables
```

### Module Responsibilities

* **`sound.pyx`**: Interacts with the SDL2 Audio subsystem via `nogil` C callbacks. Manages the active voice pool, evaluates additive partials, applies envelopes, scales headroom, and writes 32-bit floating-point samples to the audio buffer.
* **`models.py`**: Enforces type safety and structural validation using Pydantic V2 models. Defines both declarative schema models (`SoundsRoot`, `ScoreRoot`) and intermediate playback DTOs (`NoteEventDTO`, `CompiledScoreDTO`).
* **`compile.py`**: Converts musical notation (beats, note names, dynamics) into absolute start times, fundamental frequencies in Hertz, and duration in seconds based on a specified BPM.
* **`loader.py`**: Ingests external symbolic score representations via `music21`, resolving polyphonic voices, flattening parts, handling ties, and mapping tempo markings.
* **`files.py`**: Multi-tier filesystem path resolver (checking absolute paths, CWD relative paths, and script directory relative paths) with safe YAML decoding.
* **`main.py`**: Argument parsing, command dispatch, and catalog rendering.

## Data Models & Schemas

The pipeline separates declarative domain configuration from execution DTOs.

### 1. Audio Definitions (`sounds.yaml` $\to$ `SoundsRoot`)

* **`SignatureModel`**: Time signature definitions (`name`, `beats_per_measure`, `beat_unit`).
* **`BeatModel`**: Relative duration scalar normalized to a whole note ($1.0 = \text{whole note}$, $0.25 = \text{quarter note}$, $0.125 = \text{eighth note}$, etc.).
* **`NoteFrequencyModel`**: Pitch name to fundamental frequency mapping in Hertz (`REST` = 0.0 Hz; `A0` to `C8` calculated at equal temperament $A_4 = 440\text{ Hz}$).
* **`TimbreModel`**: Additive synthesis harmonic weights (up to 8 overtones), linear attack duration (`attack` in seconds), and exponential decay coefficient (`decay`).
* **`dynamics`**: Symbolic musical dynamics (`ppp` through `fff`) mapped to velocity scalars between $0.0$ and $1.0$.

### 2. Declarative Scores (`score.yaml` $\to$ `ScoreRoot`)

* **`ScoreNote`**: An individual chronological score item containing `beat`, optional `dynamic`, optional `timbre`, and either `note` (monophonic string) or `notes` (chord list).
* **`TrackEntry`**: Dedicated instrumental or polyphonic line (e.g., `left_hand`, `right_hand`) with track-level default dynamics and timbres.
* **`ScoreEntry`**: Top-level score definition containing `signature`, `bpm`, and either a sequential `notes` list or a dictionary of named `tracks`.

### 3. Pipeline DTOs

* **`NoteEventDTO`**: Atomic event emitted to the synthesis engine:
    * `start_time` (float, seconds)
    * `frequency` (float, Hz)
    * `duration` (float, seconds)
    * `pitch_name` (optional str)
    * `velocity` (float, $[0.0, 1.0]$)
    * `attack` (float, seconds)
    * `decay` (float, dimensionless rate)
    * `harmonics` (list of floats, up to 8 weights)
* **`CompiledScoreDTO`**: Container holding `ScoreMetadataDTO` and an ordered list of `NoteEventDTO` instances. Exposes `.to_event_tuples()` to marshal Python objects into native C struct buffers.

## Synthesis & DSP Architecture

The Cython engine (`sound.pyx`) runs a synchronous SDL2 audio callback operating at **48,000 Hz, 32-bit floating-point mono** (`AUDIO_F32SYS`) with a buffer size of 1024 samples.

### Voice Allocation & Polyphony

* The engine maintains a fixed pool of 32 voices (`DEF MAX_VOICES = 32`).
* Incoming events are pre-allocated in chronological order. During each audio buffer slice, pending notes whose `start_sample <= current_sample` claim an inactive voice slot.
* Notes with `frequency <= 0.0` (rests) are skipped during voice instantiation.

### Acoustic Modeling Equations

1. **Velocity to Amplitude (Stevens' Power Law)**:

Perceived acoustic loudness scales non-linearly with physical strike velocity:

$$A_{\text{base}} = v^{1.8}$$

where $v \in [0.01, 1.0]$.

2. **Dynamic Spectral Brightness**:

Pianos and acoustic instruments produce brighter timbres (richer high partials) at higher strike velocities. Each harmonic partial weight $w_h$ is attenuated or emphasized dynamically:

$$\text{brightness} = v^{0.5}$$


$$w'_h = w_h \cdot (\text{brightness})^h = w_h \cdot v^{0.5h}$$

where $h \in [0, N_{\text{harmonics}} - 1]$

3. **Envelope Generation**:

* **Linear Attack**: For sample index $s < s_{\text{attack}}$:

$$\text{env}(s) = \frac{s}{s_{\text{attack}}}$$

* **Exponential Decay**: For sample index $s \ge s_{\text{attack}}$:

$$\text{env}(s) = \exp\left(-k_{\text{decay}} \cdot \frac{s}{s_{\text{total}}}\right)$$

4. **Additive Harmonic Oscillator**:

Each voice accumulates up to 8 overtone partials:

$$V(s) = A_{\text{base}} \cdot \text{env}(s) \sum_{h=0}^{N-1} w'_h \sin\left(\phi_h(s)\right)$$

$$\phi_h(s + 1) = \phi_h(s) + \frac{2\pi \cdot f \cdot (h + 1)}{f_{\text{sample}}}$$

5. **Polyphonic Headroom Scaling**:

To prevent digital clipping and inter-modulation distortion as polyphony increases, active voices are dynamically attenuated:

$$A_{\text{mix}} = \begin{cases} 0.35 & \text{if } N_{\text{active}} \le 1 \\ \frac{0.35}{1.0 + 0.35 \cdot (N_{\text{active}} - 1)} & \text{if } N_{\text{active}} > 1 \end{cases}$$

## CLI Usage & Capabilities

The CLI is invoked via `scripts/synthesize/main.py` and exposes two primary commands: `synthesize` and `ingest`.

```bash
python main.py [-h] {synthesize,ingest} ...
```

### 1. Synthesize Declarative YAML Scores

Renders scores defined in `score.yaml` using audio definitions from `sounds.yaml`.

```bash
# Synthesize default score.yaml using default sounds.yaml
python main.py synthesize

# Synthesize custom files
python main.py synthesize --score /path/to/custom_score.yaml --sounds /path/to/custom_sounds.yaml
```

### 2. Ingest Symbolic Corpus Scores (music21)

Ingests, converts, and plays classical compositions directly through the procedural synthesis engine.

#### List Available Catalog Entries

```bash
python main.py ingest --list
```

Outputs the catalog of pre-configured corpus scores (Chopin Mazurkas, Beethoven String Quartets, Bach Chorales, Große Fuge).

#### Play a Catalog Entry

```bash
# Play Bach Chorale BWV 66.6 at default tempo
python main.py ingest --name bach_chorale_bwv66_6

# Play Beethoven Große Fuge at an accelerated tempo (130 BPM)
python main.py ingest --name beethoven_grosse_fuge_op133 --bpm 130.0

# Limit playback to the first 16 measures
python main.py ingest --name chopin_mazurka_op6_no2 --max-measures 16
```

#### Supported Score Formats

The ingestion loader automatically detects and parses the following formats via file extension or corpus path:

* **Humdrum** (`.krn`)
* **MusicXML** (`.mxl`, `.xml`)
* **ABC Notation** (`.abc`)
* **Standard MIDI** (`.mid`, `.midi`)

## Configuration Reference

### Timbre Definition (`sounds.yaml`)

```yaml
sounds:
  timbres:
    piano:
      harmonics: [1.0, 0.35, 0.10, 0.02]  # Fundamental + 3 overtones
      attack: 0.005                       # 5ms attack ramp
      decay: 2.2                          # Decay curve steepness
    reed:
      harmonics: [1.0, 0.0, 0.6, 0.0, 0.3, 0.0, 0.1]  # Odd harmonics dominant
      attack: 0.020
      decay: 1.5

```

### Multi-Track Score Structure (`score.yaml`)

```yaml
score:
  composition_id:
    signature: "four-four"
    bpm: 120.0
    tracks:
      treble_lead:
        timbre: "piano"
        default_dynamic: "mf"
        notes:
          - note: "C4"
            beat: "quarter"
          - notes: ["E4", "G4", "C5"]  # Polyphonic chord
            beat: "quarter"
            dynamic: "f"
      bass_line:
        timbre: "soft_piano"
        default_dynamic: "p"
        notes:
          - note: "C2"
            beat: "half"
```