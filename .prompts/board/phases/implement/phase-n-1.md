#### Implement: Phase n-1: Sound

**Overview**

Implement the foundational audio architecture for the engine, unifying hardware-accelerated playback of pre-rendered audio assets (`.mp3`, `.wav`) with a high-performance procedural additive synthesizer. The phase establishes an asset pipeline for indexing audio files in `/src/assets/sounds/`, integrates a non-blocking audio mixer into the Cython core, and implements interactive instrument mechanics that propagate musical events into Sprite psychological state transitions.

##### Specification

1. **Asset Pipeline & Schemas**:
   - `/src/assets/sounds/main.yaml`: Index defining audio properties across categories:
     - `music`: Streaming background audio tracks (`.mp3`) with loop boundaries and default gain.
     - `noises`: Environmental, collision, and physical interaction audio samples (`.wav`).
     - `vocals`: Creature and character verbalizations (`.wav`).
     - `timbres`: Additive synthesis instrument definitions (harmonics list, attack ramp, exponential decay coefficient).
     - `scores`: Melodic compositions and motif templates mapped to notes, durations, and dynamic values.
2. **Audio Architecture (`libs/audio/mixer.pyx`)**:
   - Unified SDL2 / `SDL_mixer` backend operating at 48,000 Hz, 32-bit float (`AUDIO_F32SYS`), stereo output.
   - Non-blocking lock-free SPSC ring buffer for passing real-time note events from the game loop to the audio thread.
   - Polyphonic additive synthesizer executing inside a `Mix_SetPostMix` callback with zero heap allocation in the audio loop.
3. **Interactive Instrument System**:
   - `InstrumentController`: Modal device mapping converting keyboard/gamepad inputs into musical pitch triggers.
   - `MelodyEvent`: Bus event emitted on note onset containing pitch, frequency, velocity, position, and source entity ID.
4. **Psychological & Ecological Mechanics (`SoundMechanics`)**:
   - Ambient sound attenuation model calculating acoustic radius and obstacle transmission loss via line clipping (`geometry.c_punctures`).
   - Melodic trie evaluator matching incoming note sequences against configured motifs.
   - Sprite psyche integration modulating `MutatorTriggers` (`frightened`, `calmed`, `attentive`) and injecting sensory events into `TransitionMechanics`.

##### Architectural Analysis I

The audio subsystem must decouple runtime synthesis from the fixed 60 Hz physics loop while maintaining strict synchronization with Sprite cognition. Calling transcendental functions per sample inside Python would drop frame rates below acceptable thresholds; thus, audio synthesis must remain in C memory via Cython, completely releasing the GIL.

Pre-recorded assets (`.wav`, `.mp3`) and synthesized timbres require distinct memory management:
- `.mp3` files stream directly from disk via `Mix_Music` to prevent loading multi-megabyte uncompressed PCM buffers into RAM.
- `.wav` files are pre-loaded into GPU-adjacent system RAM during `Registry.prewarm` as `Mix_Chunk*` pointers, indexed by asset key for instantaneous $O(1)$ playback.
- Procedural scores defined in YAML must be compiled during initialization into flat C structs (`NoteEvent`), guaranteeing that runtime score playback incurs zero parsing overhead.

To prevent audio stutter and race conditions, the engine will not use mutex locks across the Python/audio boundary. Instead, the main thread pushes note triggers into an atomic 256-slot ring buffer. The audio callback drains this buffer at sample accuracy without locking.

##### Goals

###### Goal: Zero-Allocation Audio Engine & Mixer Integration

Develop the Cython audio engine (`libs.audio.mixer`) wrapping `SDL_mixer`. Implement streaming music channels, positional SFX pooling, and a real-time additive synth inside `Mix_SetPostMix`. Replace per-sample transcendentals with recursive rotation oscillators to maximize DSP throughput.

###### Goal: Sound Registry Hydration & Property Modeling

Extend `PropertiesSchema` and `Registry` to index audio assets from `/src/assets/sounds/`. Prewarm `.wav` chunks into memory, map streaming `.mp3` paths, and compile declarative timbre/score definitions into compact binary buffers.

###### Goal: Interactive Instrument Controller & Device Context

Implement the `InstrumentController` menu and input handler. Allow entities interacting with musical objects (e.g., piano) to intercept device polling, route direct pitch triggers to the audio mixer, and emit `MelodyEvent` instances onto the engine bus.

###### Goal: SoundMechanics & Sprite Psyche Resonance

Create `SoundMechanics` within the `world` mechanics pipeline. Calculate sound propagation, distance decay, and obstacle muffling. Evaluate melodic sequence recognition via a motif trie, mutating overlapping Sprite `Psyche` states and steering behavioral intentions.

##### Tasks

**1. Task: Cython Audio Subsystem & Real-Time Mixer**

*Objective*: Build the low-level SDL_mixer audio wrapper and non-blocking additive synthesis engine in `libs/audio/mixer.pyx`.

- [ ] Subtask: Configure build pipeline in `setup.py` and `Dockerfile` to link against `SDL2_mixer`.
- [ ] Subtask: Implement `libs/audio/mixer.pyx` managing `Mix_OpenAudio`, music streaming, and SFX channels.
- [ ] Subtask: Implement a lock-free SPSC circular queue for thread-safe event passing from Python to the audio thread.
- [ ] Subtask: Port `sound.pyx` synthesis logic into a `Mix_SetPostMix` callback supporting dynamic voice allocation up to 32 voices.
- [ ] Subtask: Optimize oscillator math using recursive cosine phasors and Stevens' power law amplitude scaling.

**2. Task: Sound Models, Asset Schemas & Registry Loading**

*Objective*: Establish data structures for audio configuration and integrate asset prewarming into the application boot sequence.

- [ ] Subtask: Define `SoundProperties`, `TimbreProperties`, `ScoreProperties`, and `AudioEventDTO` models in `app/models/properties.py`.
- [ ] Subtask: Implement YAML parser logic in `app/config/loader.py` for `/src/assets/sounds/main.yaml`.
- [ ] Subtask: Update `Registry` to cache `Mix_Chunk` pointers and compile score timelines during boot and prewarming.
- [ ] Subtask: Integrate sound resource teardown and memory deallocation into `Engine.stop()` and `Registry.clear()`.

**3. Task: Interactive Instrument Mechanics & Device Mapping**

*Objective*: Enable in-game musical interaction when characters interact with instrument objects.

- [ ] Subtask: Create `InstrumentMenu` and `InstrumentController` in `app/game/menus/` supporting chromatic scale mappings.
- [ ] Subtask: Implement device context switching in `PlayerMechanics` when interacting with instrument objects.
- [ ] Subtask: Emit `MelodyEvent` objects to `Engine.bus` containing pitch, velocity, and world coordinate metadata.

**4. Task: SoundMechanics & Psychological Propagation**

*Objective*: Simulate physical sound propagation and evaluate Sprite behavioral responses to music and noise.

- [ ] Subtask: Implement `SoundMechanics` implementing `Mechanic.update()` within the `world` mechanics pipeline.
- [ ] Subtask: Implement spatial sound attenuation and obstacle occlusion checks using `geometry.c_punctures`.
- [ ] Subtask: Construct a sliding-window Trie to match active melody sequences against configured song motifs.
- [ ] Subtask: Connect motif matches and sound amplitudes to Sprite `Mutators` (`frightened`, `calmed`) to trigger intention shifts in `TransitionMechanics`.