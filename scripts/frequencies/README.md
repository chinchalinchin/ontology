# Ontology: Fourier Frequency Analysis

Audio feature extraction and spectral profile breakdown tool built for the `ontology` game engine sound pipeline. It applies the Short-Time Fourier Transform (STFT) to analyze raw audio frequency content across species, gender, and identifier voice profiles.


## 1. Mathematical Model

Given a discrete-time signal $x[n]$ sampled at rate $f_s$, the Short-Time Fourier Transform computes the localized spectrum by sliding a window function $w[n]$ across time:

$$X(m, \omega) = \sum_{n=-\infty}^{\infty} x[n] w[n - m] e^{-j \omega n}$$

- **Windowing**: A Hann window ($N = 1024$) minimizes spectral leakage across time boundaries.
- **Overlap**: A 50% hop size ($R = 512$ samples) preserves time-frequency continuity.
- **Spectral Centroid**: Represents the "center of mass" or perceived brightness of the voice signal:

$$\text{Centroid}_t = \frac{\sum_{k=0}^{K-1} f_k \vert{}X(t, f_k)\vert{}}{\sum_{k=0}^{K-1} \vert{}X(t, f_k)\vert{}}$$

- **85% Rolloff Frequency**: Frequency bin $f_r$ beneath which 85% of total spectral power resides:

$$\sum_{k=0}^{r} \vert{}X(t, f_k)\vert{}^2 = 0.85 \sum_{k=0}^{K-1} \vert{}X(t, f_k)\vert{}^2$$

---

## 2. File Naming Schema

Every analyzed file adheres to the hyphenated metadata token standard:

```text
<species>-<gender>-<identifier>-<utterance>-<index>.wav
```

* `<species>`: Creature type (`human`, `zombie`, `minotaur`).
* `<gender>`: Acoustic range bias (`male`, `female`, `androgynous`).
* `<identifier>`: Voice timbre register (`deep`, `medium`, `high`).
* `<utterance>`: Expression type (`gasp`, `grunt`, `sigh`, `strain`).
* `<index>`: Zero-padded serial index (`00`, `01`, `02`).

---

## 3. Installation

From within the `scripts/frequencies/` directory:

```bash
uv pip install -r requirements.txt
# or with standard pip:
pip install -r requirements.txt
```


## 4. CLI Usage

The script provides two commands: `decompose` and `visualize`.

### Default Execution

When `--files` is omitted, the script automatically searches for files in `sample/*` (or recurses the package tree for `.wav` files).

```bash
# Decompose default files
python main.py decompose

# Visualize default files
python main.py visualize

```

### Passing Specific Files and Globs

The `--files` argument accepts comma-separated lists and wildcard patterns (`*`, `**`):

```bash
# Glob all files under a subdirectory
python main.py decompose --files "human/female/*"

# Pass a comma-separated list of paths or globs
python main.py decompose --files "human/female/*-deep-*,human/female/*-high-*"

# Export raw JSON metrics for downstream automation
python main.py decompose --files "human/female/*" --json output_metrics.json
```

### Visualization Output

Running `visualize` writes two high-resolution `.png` files directly to `scripts/frequencies/`:

```bash
python main.py visualize --files "human/female/*"
```

1. **`profile_spectral_breakdown.png`**:
    * Compares the mean normalized Power Spectral Density (PSD in dB) across `deep`, `medium`, and `high` profiles.
    * Generates boxplots of the spectral centroids to measure acoustic register divergence.
2. **`profile_spectrograms.png`**:
    * Renders a multi-panel STFT spectrogram grid (frequencies up to 6 kHz vs. duration in seconds) categorized by identifier and utterance type (`grunt`, `strain`, `gasp`, `sigh`).