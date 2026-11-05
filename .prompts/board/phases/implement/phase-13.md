#### Implement: Phase 13: Sound

**Overview**

Implement the foundational audio architecture for the engine, unifying hardware-accelerated playback of pre-rendered audio assets (`.mp3`, `.wav`) with the procedural additive synthesizer and declarative score models developed in `scripts/synthesize`. The phase establishes `/src/assets/sounds/main.yaml` for indexing audio files and synthesis tables (`notes`, `beats`, `dynamics`, `timbres`, `scores`), integrates a lock-free Cython audio mixer (`libs/audio/mixer.pyx`), inducts LPC `instruments` (`pipe-organ`, `grand-piano`, `player-piano`, `lute`, `bongos`) into the `objects` Asset Category, and implements the `InstrumentEvent` $\to$ `InstrumentMenu` $\to$ `MelodyEvent` pipeline that generates real-time synthesized sound and propagates musical motifs into Sprite psychological state transitions.

##### Specification

1. **Asset Pipeline & Sound Schemas (`/src/assets/sounds/main.yaml`)**:
   * Unify pre-rendered audio assets and `scripts/synthesize` models under `PropertiesSchema.sounds`:
   * `music`: Streaming background audio tracks (`.mp3`) with loop boundaries and default gain.
   * `noises`: Environmental, collision, and physical interaction audio samples (`.wav`).
   * `vocals`: Creature and character verbalizations (`.wav`).
   * `notes`: Equal-temperament pitch lookup table mapping scientific pitch names (`REST`, `A0`–`C8`) to fundamental frequencies in Hz (`NoteFrequencyModel`).
   * `beats`: Whole-note normalized duration scalars (`whole: 1.0`, `dotted_quarter: 0.375`, `quarter: 0.25`, `eighth: 0.125`, `sixteenth: 0.0625`, etc. from `BeatModel`).
   * `signatures`: Time signature definitions (`beats_per_measure`, `beat_unit` from `SignatureModel`).
   * `dynamics`: Symbolic dynamic markings (`ppp: 0.15` through `fff: 1.00`) mapped to normalized velocity scalars.
   * `timbres`: Additive synthesis instrument definitions (`TimbreProperties`: up to 8 harmonic partial weights, linear `attack` ramp in seconds, exponential `decay` coefficient, and default `beat` duration) configured for LPC instruments (`grand_piano`, `pipe_organ`, `lute`, `bongos`, `reed`, `bell`).
   * `scores`: Declarative multi-track and single-track compositions (`ScoreProperties`, `TrackProperties`, `ScoreNoteProperties` ported from `scripts/synthesize/models.py`) alongside short recognizable melodic motifs.
2. **Instrument Object Taxonomy (`objects.instruments`)**:
   * Register `instruments` under `AssetCategories.OBJECTS` (`ObjectPropertyInstances.instruments`, `ObjectStateInstances.instruments`):
   * **Supported LPC Assets**: `pipe-organ`, `grand-piano`, `player-piano`, `lute`, `bongos`.
   * **`InstrumentProperties(ObjectProperties)`**: Extends `ObjectProperties` (`dimensions`, `priority`, `hitboxes`, `count`, `mass`, `materials`) with `timbre: str`, `layout: Enumerated[InstrumentLayouts]` (`chromatic`, `diatonic`, `percussion`, `player`), `octaves: Tuple[int, int] = (2, 6)`, and `default_beat: str = "quarter"`.
   * **`InstrumentState(ObjectState)`**: Extends `ObjectState` (`position`, `material`) with `octave: int = 4`, `dynamic: Enumerated[Dynamics] = "mf"`, `score: Optional[str] = None` (for `player-piano` autonomous or triggered score playback), and `switch: bool = False`.
3. **Audio Architecture (`libs/audio/mixer.pyx`)**:
   * Unified SDL2 / `SDL_mixer` backend operating at 48,000 Hz, 32-bit float (`AUDIO_F32SYS`), mono/stereo output.
   * Lock-free Single-Producer Single-Consumer (SPSC) ring buffer (`NoteEvent[256]`) for passing real-time note triggers and compiled score sequences from Python (`Engine._drain()`) to the C audio callback without holding the GIL or acquiring mutexes.
   * 32-voice polyphonic additive synthesizer ported from `scripts/synthesize/sound.pyx` executing inside `Mix_SetPostMix`, implementing Stevens' power law amplitude scaling ($A = v^{1.8}$), dynamic harmonic brightness ($w'_h = w_h \cdot v^{0.5h}$), linear attack + exponential decay envelopes, and polyphonic headroom scaling.
4. **Interactive Instrument Event & Menu Pipeline**:
   * **Step 1 (`InteractionMechanics`)**: When the Player enters the `interact` Intention while intersecting an `objects.instruments` hitbox, `InteractionMechanics` emits an `InstrumentEvent(sprite, instrument, properties)` onto `Engine.bus`.
   * **Step 2 (`InstrumentEventHandler`)**: Routes `InstrumentEvent` during `Engine._drain()`, pauses world simulation (`board.paused = True`), constructs `InstrumentContext(sprite, instrument, properties)`, instantiates `InstrumentMenu` via `Provider.menu("instrument", context)`, and pushes it onto `board.menus`.
   * **Step 3 (`InstrumentMenu` & `KeyboardGizmo`)**: Replaces an unwieldy 88-key layout with an ergonomic **13-Key Chromatic Octave (`C` to `C'`)** (8 white natural `key-white` buttons in a lower `dock` Pane + 5 staggered black accidental `key-black` buttons in an upper `dock` Pane, or 4 `drum-pad` buttons for `bongos`), augmented by `octave-down`, `octave-up`, `dynamic`, `play-score` (for `player-piano`), and `exit` control buttons.
   * **Step 4 (`InstrumentController.select`)**: Traversing `InstrumentMenu` via `MenuMechanics` and selecting a Key Button invokes `InstrumentController.select(name, menu, board, bus)`. Selecting a key combines the button's semitone/pitch selector with `context.instrument.octave`, resolves frequency, velocity, duration, and timbre from `Registry.sounds`, and pushes a `MelodyEvent` onto `Engine.bus`.
   * **Step 5 (`MelodyEventHandler`)**: Processes `MelodyEvent` in `Engine._drain()`, pushing the resolved `(start_time, freq, duration, velocity, attack, decay, harmonics)` tuple directly into `mixer.push_note()` and appending the pitch onset to the Board's acoustic buffer.
5. **Psychological & Ecological Mechanics (`SoundMechanics`)**:
   * Ambient sound attenuation model calculating acoustic radius and obstacle transmission loss via line clipping (`geometry.c_punctures`).
   * Sliding-window Melodic Trie evaluator matching played note sequences from `MelodyEvent` against configured score motifs.
   * Sprite psyche integration modulating `MutatorTriggers` (`frightened`, `calmed`, `attentive`) and injecting sensory events into `TransitionMechanics`.

##### Architectural Analysis I

The audio subsystem must decouple runtime synthesis from the fixed 60 Hz physics loop while maintaining strict synchronization with Sprite cognition. Calling transcendental functions per sample inside Python would drop frame rates below acceptable thresholds; thus, audio synthesis must remain in C memory via Cython, completely releasing the GIL.

Pre-recorded assets (`.wav`, `.mp3`) and synthesized timbres require distinct memory management:

* `.mp3` files stream directly from disk via `Mix_Music` to prevent loading multi-megabyte uncompressed PCM buffers into RAM.
* `.wav` files are pre-loaded into GPU-adjacent system RAM during `Registry.prewarm` as `Mix_Chunk*` pointers, indexed by asset key for instantaneous $O(1)$ playback.
* Procedural scores defined in YAML must be compiled during initialization into flat C structs (`NoteEvent`), guaranteeing that runtime score playback incurs zero parsing overhead.

To prevent audio stutter and race conditions, the engine will not use mutex locks across the Python/audio boundary. Instead, the main thread pushes note triggers into an atomic 256-slot ring buffer. The audio callback drains this buffer at sample accuracy without locking.

##### User Review I

Drill down on implementing the `Instrument` Object within the application using the Sound models from `scripts/synthesize`:

1. Player interacts with `Instrument`.
2. `InstrumentEvent` is thrown.
3. `InstrumentMenu` is instantiated.
4. Player traverses Menu and selects Key Widgets (special Button IDs) to play.
5. Sound is generated each time `Engine` handles a select event on one of the Key Widgets.
6. All 88 keys is overkill—scope the keyboard representation appropriately.
7. Account for the LPC Instrument assets: `pipe organ`, `grand piano`, `player piano`, `lute`, `bongos`.

##### Architectural Analysis II

###### 1. Porting `scripts/synthesize` Models into `app.models.properties` and `Registry`

In `scripts/synthesize`, audio synthesis is driven by two declarative schemas (`SoundsRoot` and `ScoreRoot`) and a time-domain compiler (`compile.score()`) that flattens hierarchical tracks and beats into chronological `NoteEventDTO` tuples:

$$e_i = \big(t_{\text{start}},\; f_0,\; \Delta t,\; v,\; t_{\text{attack}},\; k_{\text{decay}},\; [w_0, w_1, \dots, w_{n-1}]\big)$$

To integrate this cleanly into Ontology's architecture:

* **`PropertiesSchema.sounds`**: `/src/assets/sounds/main.yaml` absorbs the `sounds.yaml` and `score.yaml` structures alongside pre-rendered `.mp3`/`.wav` definitions. During Phase 1 Boot, `Loader` validates `/src/assets/sounds/main.yaml` into `SoundPropertyInstances`.
* **Compile-At-Boot Score Hydration**: During `Registry` initialization, every declarative `ScoreProperties` entry (such as `chopin_nocturne_op9_no2` for the `player-piano` or short 4–8 note gameplay motifs) is compiled via `compile.score()` into a tuple list and cached in `Registry._scores`.
* **Immediate Single-Note Resolution**: For live interactive key presses in `InstrumentMenu`, `Registry.resolve_note(pitch_name, beat_name, dynamic_name, timbre_name, bpm)` performs $O(1)$ dictionary lookups against the hydrated `notes`, `beats`, `dynamics`, and `timbres` maps, emitting a single `NoteEvent` with `start_time = 0.0` (immediate dispatch on the current audio callback sample).

###### 2. LPC Instrument Taxonomy & Timbre Specialization

The five LPC instruments (`pipe-organ`, `grand-piano`, `player-piano`, `lute`, `bongos`) share the `(objects, instruments)` taxonomy node (`ObjectPropertyInstances.instruments` and `ObjectStateInstances.instruments`) while diverging in their acoustic `TimbreProperties` and `InstrumentLayouts`:

| LPC Asset ID | Layout Type | Default Timbre | Harmonic Profile $[w_0, \dots, w_k]$ | Attack ($s$) | Decay ($k$) | Default Beat | Behavioral Mode |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `grand-piano` | `chromatic` (13 keys) | `grand_piano` | `[1.0, 0.35, 0.10, 0.02]` | `0.005` | `2.2` | `quarter` | Manual polyphonic keyboard |
| `pipe-organ` | `chromatic` (13 keys) | `pipe_organ` | `[1.0, 0.85, 0.60, 0.45, 0.30, 0.20, 0.10, 0.05]` | `0.030` | `0.35` | `half` | Sustained cathedral pipes |
| `player-piano` | `player` (13 keys + score) | `grand_piano` | `[1.0, 0.35, 0.10, 0.02]` | `0.005` | `2.2` | `quarter` | Manual play + compiled `score` playback |
| `lute` | `chromatic` (13 keys) | `lute` | `[1.0, 0.50, 0.25, 0.08, 0.02]` | `0.003` | `3.8` | `quarter` | Plucked acoustic string decay |
| `bongos` | `percussion` (4 pads) | `bongos` | `[1.0, 0.45, 0.75, 0.25, 0.15]` | `0.001` | `7.5` | `sixteenth` | 4 tuned drum pads (`C3`, `G3`, `C4`, `E4`) |

###### 3. Solving the 88-Key Problem: The 13-Key Chromatic Octave & `KeyboardGizmo`

Rendering 88 individual `Button` widgets would saturate screen real estate and require up to 87 sequential `EAST`/`WEST` traversal inputs to cross the keyboard. Instead, `InstrumentMenu` models a **single 13-key chromatic octave (`C` through `C'`)** paired with stateful octave transposition:

* **Spatial Layout & 2D Ray-Cast Traversal**:
* **Upper Row (`dock` Pane)**: 5 `key-black` Button widgets (`C#`, `D#`, `F#`, `G#`, `A#`) spaced with horizontal gaps matching the diatonic half-step topology.
* **Lower Row (`dock` Pane)**: 8 `key-white` Button widgets (`C`, `D`, `E`, `F`, `G`, `A`, `B`, `C+1`).
* **Control Bar (`dock` Pane)**: `octave-down`, `octave-up`, `dynamic-cycle` (`pp` $\to$ `ff`), optional `score-toggle` (active on `player-piano`), and `exit`.
* Because `Layout` constructs `Menu.graph` using AABB coordinate domain overlap, a player focused on `C` or `D` can press `NORTH` to focus `C#`, `SOUTH` to return to the natural row, and `EAST`/`WEST` to step cleanly across keys in $O(1)$ graph lookups.


* **Dynamic Octave Windowing**:
* `InstrumentState.octave` defaults to `4` (mapping the 13 keys to `C4`–`C5`). Selecting `octave-down` or `octave-up` mutates `context.instrument.octave` within `properties.octaves` (e.g., `[2, 6]`), enabling 5 octaves (61 distinct pitches) using only 13 key buttons.


* **Declarative Expansion via `KeyboardGizmo**`:
* Extending `Fabricator.expand()` (`Phase 04.05: Gizmos`) with `schema: keyboard` allows `/src/data/config/menus/main.yaml` to declare a single `gizmos` node for the keybed. `Fabricator` inspects `context.properties.layout` (`chromatic` vs. `percussion`) and expands it into the concrete `panes` and `buttons` (`key-white`, `key-black`, or `drum-pad`) with pre-bound `SelectBinding(selection="play_note", selector="<note_offset>")` instances.

###### 4. End-to-End Event Flow & Pause-Safe Acoustic Evaluation

```
[PlayerMechanics] --(interact with Instrument)--> bus.append(InstrumentEvent)
       │
[Engine._drain()] --> InstrumentEventHandler.handle()
       │                ├─ board.paused = True
       │                ├─ ctx = InstrumentContext(sprite, instrument, properties)
       │                └─ board.menus.append(Provider.menu("instrument", ctx))
       ▼
[MenuMechanics]   --(player traverses graph & presses SELECT on Key Button)-->
       │
[InstrumentController.select()]
       │                ├─ resolves pitch = f"{pitch_class}{ctx.instrument.octave}"
       │                └─ bus.append(MelodyEvent(pitch, freq, dur, vel, timbre, pos, source))
       ▼
[Engine._drain()] --> MelodyEventHandler.handle()
                        ├─ libs.audio.mixer.push_note(freq, dur, vel, attack, decay, harmonics)
                        └─ board.acoustics.append(MelodyEvent)  # Consumed by SoundMechanics
```

Because modal menus set `board.paused = True` (which suspends the `Engine.world` pipeline while keeping `Engine.core` active), `MelodyEventHandler` executes inside `Engine._drain()`—which runs every tick regardless of `board.paused`. This guarantees instantaneous audio synthesis on every Key Widget selection while the world is paused, while queuing emitted `MelodyEvent` payloads onto `board.acoustics` (or evaluating the motif Trie immediately) so nearby Sprites react to the performance.

##### Goals

###### Goal: Zero-Allocation Cython Audio Mixer & `sound.pyx` Integration

Port the procedural synthesis engine from `scripts/synthesize/sound.pyx` into `libs/audio/mixer.pyx` alongside `SDL_mixer` channel management. Replace the blocking `while not synth.finished: SDL_Delay(20)` loop from the standalone CLI script with a non-blocking `Mix_SetPostMix` callback that drains a lock-free 256-slot SPSC ring buffer of `NoteEvent` structs:

```cython
# libs/audio/mixer.pyx
DEF MAX_VOICES = 32
DEF MAX_HARMONICS = 8
DEF RING_BUFFER_SIZE = 256

cdef struct NoteEvent:
    int start_sample      # 0 for immediate interactive key press; >0 for scheduled score notes
    int total_samples
    float freq
    float velocity
    float attack
    float decay
    int num_harmonics
    float harmonics[MAX_HARMONICS]

cdef struct SynthState:
    int sample_rate
    int current_sample
     int write_idx
    int read_idx
    NoteEvent ring[RING_BUFFER_SIZE]
    Voice voices[MAX_VOICES]

cpdef void push_note(
    float start_delay,
    float freq,
    float duration,
    float velocity,
    float attack,
    float decay,
    list harmonics
):
    """Pushes a single note event from MelodyEventHandler into the lock-free SPSC ring buffer."""
    cdef int next_w = ( _synth.write_idx + 1 ) & (RING_BUFFER_SIZE - 1)
    if next_w == _synth.read_idx:
        return  # Buffer full; drop oldest/excess without blocking GIL
    # Populate _synth.ring[_synth.write_idx] and advance _synth.write_idx = next_w

```

###### Goal: Sound Schema Hydration, Score Compilation & Instrument Models

Unify the `scripts/synthesize/models.py` definitions with `app/models/properties/` and `app/models/state/`. Add `instruments` to `ObjectPropertyInstances` and `ObjectStateInstances`, and add `sounds` to `PropertiesSchema`:

```python
# src/app/models/properties/sounds.py
@dataclass(slots=True)
class TimbreProperties:
    harmonics: List[float] = field(default_factory=lambda: [1.0, 0.35, 0.10, 0.02])
    attack: float = 0.005
    decay: float = 2.2
    beat: str = "quarter"

@dataclass(slots=True)
class ScoreNoteProperties:
    beat: str
    note: Optional[Union[str, List[str]]] = None
    notes: Optional[List[str]] = None
    dynamic: Optional[str] = None
    timbre: Optional[str] = None

@dataclass(slots=True)
class InstrumentProperties(ObjectProperties):
    timbre: str = "grand_piano"
    layout: Enumerated[InstrumentLayouts] = InstrumentLayouts.CHROMATIC.value
    octaves: Tuple[int, int] = (2, 6)
    default_beat: str = "quarter"

# src/app/models/state/assets.py
@dataclass(slots=True)
class InstrumentState(ObjectState):
    octave: int = 4
    dynamic: Enumerated[Dynamics] = Dynamics.MF.value
    score: Optional[str] = None
    switch: bool = False

```

###### Goal: `InstrumentEvent`, `InstrumentMenu`, & 13-Key `InstrumentController`

Implement the complete interactive lifecycle when a Player interacts with an LPC Instrument Object (`pipe-organ`, `grand-piano`, `player-piano`, `lute`, `bongos`):

```python
# src/app/game/menus/controllers/instrument.py
class InstrumentController(MenuController):
    """
    Handles key widget selections, octave transposition, dynamic cycling,
    and autonomous score triggers inside the InstrumentMenu.
    """
    def select(self, name: str, menu: Menu, board: Board, bus: collections.deque) -> None:
        widget = menu.widgets.get(name)
        if not widget or not widget.binding:
            return

        ctx: InstrumentContext = menu.context
        action = widget.binding.selection
        selector = widget.binding.selector

        if action == Selections.PLAY_NOTE.value:
            # Resolve pitch (e.g. selector="C#" + octave=4 -> "C#4", or "+12" -> "C5")
            pitch_name = self._resolve_pitch(selector, ctx.instrument.octave)
            note_dto = ctx.registry.resolve_note(
                pitch_name=pitch_name,
                beat_name=ctx.properties.default_beat,
                dynamic_name=ctx.instrument.dynamic,
                timbre_name=ctx.properties.timbre,
            )
            bus.append(MelodyEvent(
                source=ctx.sprite.name,
                layer=ctx.instrument.layer,
                position=ctx.instrument.position,
                note=note_dto,
            ))
        elif action == Selections.OCTAVE_UP.value:
            max_oct = ctx.properties.octaves[1]
            ctx.instrument.octave = min(max_oct, ctx.instrument.octave + 1)
            bus.append(UpdateEvent(menu=menu.id, target="octave-display"))
        elif action == Selections.OCTAVE_DOWN.value:
            min_oct = ctx.properties.octaves[0]
            ctx.instrument.octave = max(min_oct, ctx.instrument.octave - 1)
            bus.append(UpdateEvent(menu=menu.id, target="octave-display"))
        elif action == Selections.PLAY_SCORE.value and ctx.instrument.score:
            bus.append(MelodyEvent(
                source=ctx.instrument.name,
                layer=ctx.instrument.layer,
                position=ctx.instrument.position,
                score_key=ctx.instrument.score,
            ))
        elif action == Selections.EXIT.value:
            bus.append(TerminalEvent())

```

###### Goal: `SoundMechanics` & Sprite Psyche Resonance

Create `SoundMechanics` to drain `board.acoustics` (populated by `MelodyEventHandler`), compute spatial attenuation and obstacle occlusion via `geometry.c_punctures`, and advance a sliding-window Melodic Trie that matches played note sequences against configured score motifs to trigger Sprite `MutatorTriggers` (`calmed`, `frightened`, `attentive`).

##### Tasks

**1. Task: Cython Audio Subsystem & Real-Time Additive Synthesizer**

*Objective*: Build `libs/audio/mixer.pyx` wrapping `SDL2_mixer` and porting the `scripts/synthesize/sound.pyx` polyphonic additive synthesis engine into a non-blocking callback.

* [ ] Subtask: Configure build pipeline in `setup.py`, `setup.cicd.py`, and `Dockerfile` to link against `SDL2` and `SDL2_mixer`.
* [ ] Subtask: Implement `libs/audio/mixer.pyx` managing `Mix_OpenAudio` (48,000 Hz, `AUDIO_F32SYS`), streaming `Mix_Music` channels, and `Mix_Chunk` SFX channels.
* [ ] Subtask: Implement a lock-free 256-slot SPSC circular ring buffer (`NoteEvent` C structs) with `push_note()` and `push_score()` Cython interfaces.
* [ ] Subtask: Port `sound.pyx` voice allocation (`MAX_VOICES = 32`, `MAX_HARMONICS = 8`), Stevens' power law velocity scaling ($v^{1.8}$), dynamic brightness ($v^{0.5h}$), and linear-attack/exponential-decay envelopes into a `Mix_SetPostMix` `nogil` callback.
* [ ] Subtask: Add headless/CI audio driver fallback (`SDL_AUDIODRIVER=dummy`) so unit and integration tests execute without physical audio hardware.

**2. Task: Sound & Instrument Models, Asset Schemas & Registry Compilation**

*Objective*: Port `scripts/synthesize` data models into `app/models/`, induct `objects.instruments`, and compile declarative scores during `Registry` initialization.

* [ ] Subtask: Add `INSTRUMENTS = "instruments"` to `AssetInstances`, `SOUNDS = "sounds"` to `AssetCategories`, and `InstrumentLayouts`, `Dynamics`, and `Selections` (`PLAY_NOTE`, `OCTAVE_UP`, `OCTAVE_DOWN`, `PLAY_SCORE`) to `app/static/semantics.py`.
* [ ] Subtask: Define `TimbreProperties`, `SignatureProperties`, `ScoreNoteProperties`, `TrackProperties`, `ScoreProperties`, `SoundPropertyInstances`, and `NoteEventDTO` in `app/models/properties/sounds.py` and attach `sounds` to `PropertiesSchema`.
* [ ] Subtask: Define `InstrumentProperties(ObjectProperties)` and `InstrumentState(ObjectState)` and register `instruments` in `ObjectPropertyInstances`, `ObjectStateInstances`, and `/src/data/config/recipes/main.yaml`.
* [ ] Subtask: Populate `/src/assets/sounds/main.yaml` with the equal-temperament `notes` table (`REST`, `A0`–`C8`), `beats`, `dynamics`, LPC instrument `timbres` (`grand_piano`, `pipe_organ`, `lute`, `bongos`), and declarative `scores` (including `chopin_nocturne_op9_no2` and gameplay motifs).
* [ ] Subtask: Configure LPC instrument assets (`pipe-organ`, `grand-piano`, `player-piano`, `lute`, `bongos`) in `/src/assets/objects/main.yaml` and key button widgets (`key-white`, `key-black`, `drum-pad`) in `/src/assets/widgets/main.yaml`.
* [ ] Subtask: Port `scripts/synthesize/compile.py` into `Registry` to pre-compile `ScoreProperties` into flat `NoteEventDTO` tuple buffers and expose `Registry.resolve_note()` for $O(1)$ single-note lookup.

**3. Task: `InstrumentEvent`, `InstrumentMenu`, `KeyboardGizmo` & `InstrumentController**`

*Objective*: Implement the 5-step interactive instrument workflow from Player interaction to Key Widget selection and sound synthesis.

* [ ] Subtask: Define `InstrumentEvent` and `MelodyEvent` in `app/game/menus/events.py` and `InstrumentContext(sprite, instrument, properties)` in `app/game/menus/contexts.py`.
* [ ] Subtask: Implement `InstrumentEventHandler` and `MelodyEventHandler` in `app/game/menus/handlers.py` and register both in `Engine.handlers`.
* [ ] Subtask: Update `PlayerMechanics` to emit `InstrumentEvent` onto `Engine.bus` when the Player triggers `interact` while intersecting an `objects.instruments` asset.
* [ ] Subtask: Extend `Fabricator.expand()` (`app/services/generators/menus/fabricator.py`) with a `keyboard` Gizmo schema that generates the staggered 13-key chromatic button layout (5 `key-black` buttons over 8 `key-white` buttons) for `chromatic` instruments and a 4-pad layout for `percussion` (`bongos`).
* [ ] Subtask: Define the `instrument` menu configuration in `/src/data/config/menus/main.yaml` containing the `keyboard` Gizmo pane, octave shift buttons (`octave-down`, `octave-up`), dynamic selector, `player-piano` score button (`play-score`), and `exit` button.
* [ ] Subtask: Implement `InstrumentController.select()` in `app/game/menus/controllers/instrument.py` to resolve selected Key Widget pitches against `InstrumentState.octave`, emit `MelodyEvent` payloads to `Engine.bus`, and handle octave/dynamic state mutations.

**4. Task: `SoundMechanics`, Spatial Attenuation & Melodic Trie Resonance**

*Objective*: Simulate physical sound propagation and evaluate Sprite behavioral responses to live player melodies and environmental audio.

* [ ] Subtask: Implement `SoundMechanics` in `app/game/logic/mechanics/world/sound.py` consuming queued `MelodyEvent` payloads from the Board acoustic buffer.
* [ ] Subtask: Implement distance attenuation ($I(r) = I_0 / (1 + \alpha r^2)$) and obstacle transmission muffling across layer hitboxes using `geometry.c_punctures`.
* [ ] Subtask: Construct a sliding-window Melodic Trie matcher to detect completed motif sequences from live `InstrumentMenu` key selections.
* [ ] Subtask: Connect motif matches and acoustic amplitude thresholds to Sprite `MutatorTriggers` (`frightened`, `calmed`, `attentive`) and `Expressions` to drive intention transitions in `TransitionMechanics`.