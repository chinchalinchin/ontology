"""
@domain.script
@script.frequencies

# Ontology: Script - Fourier Frequency Analysis
"""

import argparse
from dataclasses import asdict, dataclass
import glob
import json
from pathlib import Path
import re
import struct
import sys
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent


@dataclass
class AudioMetadata:
  path: Path
  filename: str
  species: str
  gender: str
  identifier: str
  utterance: str
  index: str


@dataclass
class FrequencyMetrics:
  sample_rate: int
  duration_sec: float
  total_samples: int
  peak_frequency_hz: float
  mean_spectral_centroid_hz: float
  spectral_rolloff_85_hz: float
  frequency_resolution_hz: float
  mean_psd: List[float]
  frequency_bins: List[float]


def parse_metadata(file_path: Path) -> AudioMetadata:
  """
    Parses metadata from filename following the schema:
    <species>-<gender>-<identifier>-<utterance>-<index>.wav
    """
  stem = file_path.stem
  match = re.match(
      r"^(?P<species>[a-zA-Z0-9]+)-(?P<gender>[a-zA-Z0-9]+)-(?P<identifier>[a-zA-Z0-9]+)-(?P<utterance>[a-zA-Z0-9]+)-(?P<index>\d+)$",
      stem,
  )
  if match:
    data = match.groupdict()
    return AudioMetadata(
        path=file_path,
        filename=file_path.name,
        species=data["species"],
        gender=data["gender"],
        identifier=data["identifier"],
        utterance=data["utterance"],
        index=data["index"],
    )

  parts = stem.split("-")
  if len(parts) >= 5:
    return AudioMetadata(
        path=file_path,
        filename=file_path.name,
        species=parts[0],
        gender=parts[1],
        identifier=parts[2],
        utterance=parts[3],
        index=parts[4],
    )

  return AudioMetadata(
      path=file_path,
      filename=file_path.name,
      species="unknown",
      gender="unknown",
      identifier="unknown",
      utterance="unknown",
      index="00",
  )


def resolve_file_paths(files_arg: Optional[str] = None) -> List[Path]:
  """
    Resolves file paths from comma-separated strings or globs.
    Defaults to 'sample/*' or scans the script directory for .wav files.
    """
  matched_paths: List[Path] = []

  if files_arg:
    patterns = [p.strip() for p in files_arg.split(",") if p.strip()]
    for pattern in patterns:
      expanded = glob.glob(pattern, recursive=True)
      if not expanded:
        expanded = glob.glob(str(SCRIPT_DIR / pattern), recursive=True)

      if expanded:
        matched_paths.extend(
            [Path(p).resolve() for p in expanded if p.endswith(".wav")]
        )
      else:
        p = Path(pattern)
        if p.is_file() and p.suffix.lower() == ".wav":
          matched_paths.append(p.resolve())
  else:
    default_sample_dir = SCRIPT_DIR / "sample"
    cwd_sample_dir = Path.cwd() / "sample"

    if default_sample_dir.exists():
      matched_paths.extend(default_sample_dir.glob("**/*.wav"))
    elif cwd_sample_dir.exists():
      matched_paths.extend(cwd_sample_dir.glob("**/*.wav"))
    else:
      matched_paths.extend(SCRIPT_DIR.glob("**/*.wav"))

  return sorted(list(set(matched_paths)), key=lambda x: str(x))


def load_audio(file_path: Path) -> Tuple[int, np.ndarray]:
  """
    Parses a RIFF WAVE file directly, supporting integer PCM (format 1),
    IEEE float (format 3), and WAVE_FORMAT_EXTENSIBLE (format 0xFFFE).
    Converts multi-channel audio to mono float64 in [-1.0, 1.0].
    """
  raw = file_path.read_bytes()
  if len(raw) < 12 or raw[:4] not in (b"RIFF", b"RF64") or raw[8:12] != b"WAVE":
    raise ValueError(f"Invalid RIFF WAVE header in {file_path}")

  offset = 12
  fmt_tag = None
  n_channels = 1
  sample_rate = 0
  bits_per_sample = 0
  data_bytes = b""

  while offset + 8 <= len(raw):
    chunk_id = raw[offset : offset + 4]
    chunk_size = struct.unpack_from("<I", raw, offset + 4)[0]
    chunk_start = offset + 8
    chunk_end = min(chunk_start + chunk_size, len(raw))

    if chunk_id == b"fmt ":
      fmt_tag, n_channels, sample_rate, _, _, bits_per_sample = (
          struct.unpack_from("<HHIIHH", raw, chunk_start)
      )
      if fmt_tag == 0xFFFE and (chunk_end - chunk_start) >= 26:
        fmt_tag = struct.unpack_from("<H", raw, chunk_start + 24)[0]
    elif chunk_id == b"data":
      data_bytes = raw[chunk_start:chunk_end]
      break

    offset = chunk_end + (chunk_size & 1)

  if fmt_tag is None or not data_bytes:
    raise ValueError(f"Missing 'fmt ' or 'data' chunk in {file_path}")

  if fmt_tag == 3:  # WAVE_FORMAT_IEEE_FLOAT
    if bits_per_sample == 32:
      data = np.frombuffer(data_bytes, dtype="<f4").astype(np.float64)
    elif bits_per_sample == 64:
      data = np.frombuffer(data_bytes, dtype="<f8").copy()
    else:
      raise ValueError(
          f"Unsupported IEEE float bit depth ({bits_per_sample}) in {file_path}"
      )
  elif fmt_tag == 1:  # WAVE_FORMAT_PCM
    if bits_per_sample == 8:
      data = (
          np.frombuffer(data_bytes, dtype=np.uint8).astype(np.float64) - 128.0
      ) / 128.0
    elif bits_per_sample == 16:
      data = np.frombuffer(data_bytes, dtype="<i2").astype(np.float64) / 32768.0
    elif bits_per_sample == 24:
      raw_u8 = np.frombuffer(data_bytes, dtype=np.uint8).reshape(-1, 3)
      signed_int = (
          raw_u8[:, 0].astype(np.int32)
          | (raw_u8[:, 1].astype(np.int32) << 8)
          | (raw_u8[:, 2].astype(np.int8).astype(np.int32) << 16)
      )
      data = signed_int.astype(np.float64) / 8388608.0
    elif bits_per_sample == 32:
      data = (
          np.frombuffer(data_bytes, dtype="<i4").astype(np.float64)
          / 2147483648.0
      )
    else:
      raise ValueError(
          f"Unsupported PCM bit depth ({bits_per_sample}) in {file_path}"
      )
  else:
    raise ValueError(
        f"Unsupported WAVE format tag ({fmt_tag:#06x}) in {file_path}"
    )

  if n_channels > 1:
    data = data.reshape(-1, n_channels).mean(axis=1)

  return sample_rate, data


def compute_stft(
    data: np.ndarray,
    sample_rate: int,
    nperseg: int = 1024,
    noverlap: int = 512,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
  """
    Computes Short-Time Fourier Transform using vectorized NumPy sliding windows.
    Returns:
        f: 1D array of sample frequencies (Hz)
        t: 1D array of segment times (sec)
        Zxx: 2D complex STFT matrix of shape (frequencies, time_segments)
    """
  step = nperseg - noverlap
  if len(data) < nperseg:
    data = np.pad(data, (0, nperseg - len(data)))

  n = np.arange(nperseg, dtype=np.float64)
  window = 0.5 - 0.5 * np.cos(2.0 * np.pi * n / nperseg)
  scale = 1.0 / np.sum(window)

  windows = np.lib.stride_tricks.sliding_window_view(data, nperseg)[::step]
  windowed_segments = windows * window

  Zxx = np.fft.rfft(windowed_segments, axis=1).T * scale
  f = np.fft.rfftfreq(nperseg, d=1.0 / sample_rate)
  t = (np.arange(windows.shape[0]) * step + (nperseg / 2.0)) / sample_rate

  return f, t, Zxx


def extract_frequency_metrics(
    data: np.ndarray,
    sample_rate: int,
    nperseg: int = 1024,
    noverlap: int = 512,
) -> FrequencyMetrics:
  """
    Calculates spectral statistics and STFT properties.
    """
  duration = len(data) / sample_rate
  f, _, Zxx = compute_stft(data, sample_rate, nperseg=nperseg, noverlap=noverlap)
  magnitude = np.abs(Zxx)

  mean_psd = np.mean(magnitude, axis=1)
  peak_idx = int(np.argmax(mean_psd))
  peak_freq = float(f[peak_idx])

  eps = 1e-10
  spectral_sum = np.sum(magnitude, axis=0)
  centroids = np.sum(f[:, None] * magnitude, axis=0) / np.maximum(
      spectral_sum, eps
  )
  mean_centroid = float(np.mean(centroids))

  total_energy = np.sum(mean_psd)
  cumulative_energy = np.cumsum(mean_psd)
  rolloff_idx = int(np.searchsorted(cumulative_energy, 0.85 * total_energy))
  rolloff_idx = min(rolloff_idx, len(f) - 1)
  rolloff_freq = float(f[rolloff_idx])

  return FrequencyMetrics(
      sample_rate=sample_rate,
      duration_sec=duration,
      total_samples=len(data),
      peak_frequency_hz=peak_freq,
      mean_spectral_centroid_hz=mean_centroid,
      spectral_rolloff_85_hz=rolloff_freq,
      frequency_resolution_hz=float(sample_rate / nperseg),
      mean_psd=mean_psd.tolist(),
      frequency_bins=f.tolist(),
  )


def run_decompose(files: List[Path], output_json: Optional[str] = None) -> None:
  if not files:
    print(
        "Error: No .wav files found matching the target criteria.",
        file=sys.stderr,
    )
    sys.exit(1)

  print(f"\nDecomposing {len(files)} audio file(s) via STFT...\n")
  print(
      f"{'Species':<10} {'Gender':<8} {'Identifier':<12} {'Utterance':<10}"
      f" {'Dur (s)':<8} {'Peak (Hz)':<12} {'Centroid (Hz)':<14}"
      f" {'Rolloff 85% (Hz)':<16} {'Filename'}"
  )
  print("-" * 105)

  profile_stats: Dict[str, Dict[str, List[float]]] = {}
  json_records = []

  for file_path in files:
    meta = parse_metadata(file_path)
    sample_rate, data = load_audio(file_path)
    if len(data) == 0:
      continue

    metrics = extract_frequency_metrics(data, sample_rate)

    print(
        f"{meta.species:<10} {meta.gender:<8} {meta.identifier:<12}"
        f" {meta.utterance:<10} {metrics.duration_sec:<8.2f}"
        f" {metrics.peak_frequency_hz:<12.1f}"
        f" {metrics.mean_spectral_centroid_hz:<14.1f}"
        f" {metrics.spectral_rolloff_85_hz:<16.1f} {meta.filename}"
    )

    ident = meta.identifier
    if ident not in profile_stats:
      profile_stats[ident] = {"peak": [], "centroid": [], "rolloff": []}
    profile_stats[ident]["peak"].append(metrics.peak_frequency_hz)
    profile_stats[ident]["centroid"].append(metrics.mean_spectral_centroid_hz)
    profile_stats[ident]["rolloff"].append(metrics.spectral_rolloff_85_hz)

    json_records.append({
        "metadata": asdict(meta),
        "metrics": {
            "sample_rate": metrics.sample_rate,
            "duration_sec": metrics.duration_sec,
            "peak_frequency_hz": metrics.peak_frequency_hz,
            "mean_spectral_centroid_hz": metrics.mean_spectral_centroid_hz,
            "spectral_rolloff_85_hz": metrics.spectral_rolloff_85_hz,
        },
    })

  print("-" * 105)
  print("\nIdentifier Profile Aggregate Summary (Averages):")
  print(
      f"{'Identifier':<15} {'Samples':<10} {'Avg Peak (Hz)':<18} "
      f"{'Avg Centroid (Hz)':<20} {'Avg Rolloff (Hz)':<18}"
  )
  print("-" * 81)
  for ident, stats in sorted(profile_stats.items()):
    count = len(stats["peak"])
    print(
        f"{ident:<15} {count:<10} {np.mean(stats['peak']):<18.1f} "
        f"{np.mean(stats['centroid']):<20.1f}"
        f" {np.mean(stats['rolloff']):<18.1f}"
    )
  print("-" * 81)

  if output_json:
    out_path = Path(output_json)
    with open(out_path, "w", encoding="utf-8") as f:
      json.dump(json_records, f, indent=2, default=str)
    print(f"\nExported raw decomposition metrics to: {out_path.resolve()}")


def run_visualize(files: List[Path]) -> None:
  if not files:
    print(
        "Error: No .wav files found matching the target criteria.",
        file=sys.stderr,
    )
    sys.exit(1)

  print(f"\nProcessing visual frequency analysis for {len(files)} files...")

  grouped_profiles: Dict[str, List[Tuple[AudioMetadata, int, np.ndarray]]] = {}
  for path in files:
    meta = parse_metadata(path)
    sr, audio = load_audio(path)
    if len(audio) == 0:
      continue
    grouped_profiles.setdefault(meta.identifier, []).append((meta, sr, audio))

  if not grouped_profiles:
    print("Error: No valid audio samples extracted.", file=sys.stderr)
    return

  color_map = {"deep": "#1f77b4", "medium": "#2ca02c", "high": "#d62728"}
  default_colors = ["#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]

  # Figure 1: Spectral Profile & Centroid Boxplot
  fig, (ax_psd, ax_box) = plt.subplots(1, 2, figsize=(14, 6))
  profile_centroids: Dict[str, List[float]] = {}

  for idx, (ident, samples) in enumerate(sorted(grouped_profiles.items())):
    c = color_map.get(ident.lower(), default_colors[idx % len(default_colors)])
    psd_list = []
    centroids = []
    freq_axis = None

    for _, sr, audio in samples:
      f, _, Zxx = compute_stft(audio, sr)
      mag = np.abs(Zxx)
      psd_list.append(np.mean(mag, axis=1))
      if freq_axis is None:
        freq_axis = f

      centroid = np.sum(f[:, None] * mag, axis=0) / np.maximum(
          np.sum(mag, axis=0), 1e-10
      )
      centroids.append(float(np.mean(centroid)))

    if psd_list and freq_axis is not None:
      min_len = min(len(p) for p in psd_list)
      avg_psd = np.mean([p[:min_len] for p in psd_list], axis=0)
      f_plot = freq_axis[:min_len]

      avg_psd_db = 20.0 * np.log10(np.maximum(avg_psd, 1e-6))
      avg_psd_db -= np.max(avg_psd_db)

      mask = f_plot <= 8000
      ax_psd.plot(
          f_plot[mask],
          avg_psd_db[mask],
          label=f"{ident.capitalize()} (n={len(samples)})",
          color=c,
          lw=2,
      )

    profile_centroids[ident] = centroids

  ax_psd.set_title(
      "Mean Spectral Profile by Identifier", fontsize=12, fontweight="bold"
  )
  ax_psd.set_xlabel("Frequency (Hz)")
  ax_psd.set_ylabel("Normalized Magnitude (dB)")
  ax_psd.grid(True, linestyle="--", alpha=0.6)
  ax_psd.legend(loc="upper right")

  box_labels = list(profile_centroids.keys())
  box_data = [profile_centroids[k] for k in box_labels]
  bp = ax_box.boxplot(
      box_data,
      tick_labels=[k.capitalize() for k in box_labels],
      patch_artist=True,
  )
  for patch, label in zip(bp["boxes"], box_labels):
    patch.set_facecolor(color_map.get(label.lower(), "#7f7f7f"))
    patch.set_alpha(0.7)

  ax_box.set_title(
      "Spectral Centroid Separation", fontsize=12, fontweight="bold"
  )
  ax_box.set_ylabel("Frequency (Hz)")
  ax_box.grid(True, linestyle="--", alpha=0.6)

  fig.tight_layout()
  comp_plot_path = SCRIPT_DIR / "profile_spectral_breakdown.png"
  fig.savefig(comp_plot_path, dpi=300)
  plt.close(fig)
  print(f"Saved: {comp_plot_path.resolve()}")

  # Figure 2: STFT Spectrogram Matrix
  target_utterances = ["grunt", "strain", "gasp", "sigh"]
  identifiers = [k for k in ["deep", "medium", "high"] if k in grouped_profiles]
  if not identifiers:
    identifiers = list(grouped_profiles.keys())[:3]

  nrows, ncols = len(identifiers), len(target_utterances)
  fig_spec, axes = plt.subplots(
      nrows, ncols, figsize=(4 * ncols, 3 * nrows), sharex=False, sharey=True
  )
  axes = np.atleast_2d(axes)
  if nrows == 1 and ncols > 1:
    axes = axes.reshape(1, ncols)
  elif ncols == 1 and nrows > 1:
    axes = axes.reshape(nrows, 1)

  for row_idx, ident in enumerate(identifiers):
    utterance_map = {
        m.utterance: (sr, aud) for m, sr, aud in grouped_profiles[ident]
    }
    for col_idx, utt in enumerate(target_utterances):
      ax = axes[row_idx, col_idx]
      if utt in utterance_map:
        sr, aud = utterance_map[utt]
        f, t, Zxx = compute_stft(aud, sr)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(Zxx), 1e-5))
        f_mask = f <= 6000
        ax.pcolormesh(
            t, f[f_mask], mag_db[f_mask, :], shading="gouraud", cmap="magma"
        )
      else:
        ax.text(0.5, 0.5, "N/A", ha="center", va="center", color="gray")

      if row_idx == 0:
        ax.set_title(utt.upper(), fontsize=11, fontweight="bold")
      if col_idx == 0:
        ax.set_ylabel(
            f"{ident.capitalize()}\nFreq (Hz)", fontsize=10, fontweight="bold"
        )
      ax.set_ylim(0, 6000)
      if row_idx == nrows - 1:
        ax.set_xlabel("Time (s)", fontsize=9)

  fig_spec.suptitle(
      "STFT Spectrogram Matrix by Identifier and Utterance",
      fontsize=14,
      fontweight="bold",
  )
  fig_spec.tight_layout(rect=[0, 0, 1, 0.96])
  spec_plot_path = SCRIPT_DIR / "profile_spectrograms.png"
  fig_spec.savefig(spec_plot_path, dpi=300)
  plt.close(fig_spec)
  print(f"Saved: {spec_plot_path.resolve()}\n")


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      prog="frequencies",
      description=(
          "Ontology: Short-Time Fourier Transform (STFT) Frequency Decomposer"
          " and Visualizer"
      ),
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  parser_decompose = subparsers.add_parser(
      "decompose",
      help="Perform STFT frequency decomposition and print acoustic metrics.",
  )
  parser_decompose.add_argument(
      "--files",
      type=str,
      default=None,
      help=(
          "Comma-separated list of paths or glob patterns (e.g."
          " 'sample/male/*', 'sample/*')."
      ),
  )
  parser_decompose.add_argument(
      "--json",
      type=str,
      default=None,
      help="Optional path to output raw decomposition metrics as JSON.",
  )

  parser_visualize = subparsers.add_parser(
      "visualize",
      help="Generate STFT spectrograms and frequency breakdown graphs as PNGs.",
  )
  parser_visualize.add_argument(
      "--files",
      type=str,
      default=None,
      help=(
          "Comma-separated list of paths or glob patterns (e.g."
          " 'sample/male/*', 'sample/*')."
      ),
  )

  return parser


def main() -> None:
  parser = build_arg_parser()
  args = parser.parse_args()
  files = resolve_file_paths(args.files)

  if args.command == "decompose":
    run_decompose(files, output_json=args.json)
  elif args.command == "visualize":
    run_visualize(files)


if __name__ == "__main__":
  main()